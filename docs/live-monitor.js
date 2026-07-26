(() => {
  const REQUEST_HEADER = 'X-ServiceTracer-Request-ID';
  const HEALTH_INTERVAL_MS = 15000;
  const HEALTH_TIMEOUT_MS = 6000;
  const SOURCE_REF_PATTERN = /^[0-9a-f]{40}$/;
  const originalFetch = window.fetch.bind(window);

  const monitor = {
    runUrl: '',
    healthUrl: '',
    timer: null,
    polling: false,
  };

  const elements = {
    panel: document.querySelector('#live-path-monitor'),
    state: document.querySelector('#monitor-state'),
    browser: document.querySelector('#monitor-browser'),
    endpoint: document.querySelector('#monitor-endpoint'),
    api: document.querySelector('#monitor-api'),
    scope: document.querySelector('#monitor-scope'),
    vm: document.querySelector('#monitor-vm'),
    location: document.querySelector('#monitor-location'),
    sourceRef: document.querySelector('#monitor-source-ref'),
    latency: document.querySelector('#monitor-latency'),
    checkedAt: document.querySelector('#monitor-checked-at'),
    requestId: document.querySelector('#monitor-request-id'),
    transaction: document.querySelector('#monitor-transaction'),
  };

  function setMonitorState(label, stateName) {
    if (!elements.state) {
      return;
    }
    elements.state.textContent = label;
    elements.state.classList.remove(
      'monitor-state-neutral',
      'monitor-state-healthy',
      'monitor-state-warning',
    );
    elements.state.classList.add(`monitor-state-${stateName}`);
  }

  function setText(element, value, fallback = 'Not observed') {
    if (element) {
      element.textContent = value || fallback;
    }
  }

  function formatClock(value = new Date()) {
    return new Intl.DateTimeFormat(undefined, {
      hour: 'numeric',
      minute: '2-digit',
      second: '2-digit',
    }).format(value);
  }

  function shortRef(value) {
    return SOURCE_REF_PATTERN.test(value || '') ? value.slice(0, 12) : 'Unverified';
  }

  function makeRequestId() {
    if (window.crypto && typeof window.crypto.randomUUID === 'function') {
      return window.crypto.randomUUID();
    }
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (character) => {
      const random = Math.floor(Math.random() * 16);
      const value = character === 'x' ? random : ((random & 0x3) | 0x8);
      return value.toString(16);
    });
  }

  function requestDetails(input, options = {}) {
    const rawUrl = input instanceof Request ? input.url : input;
    const method = (
      options.method
      || (input instanceof Request ? input.method : 'GET')
      || 'GET'
    ).toUpperCase();
    return {
      url: new URL(rawUrl, window.location.href),
      method,
    };
  }

  function isRunRequest(details) {
    return details.method === 'POST' && details.url.pathname.endsWith('/api/demo/run');
  }

  function deriveHealthUrl(runUrl) {
    const url = new URL(runUrl, window.location.href);
    url.pathname = url.pathname.endsWith('/api/demo/run')
      ? url.pathname.replace(/\/api\/demo\/run$/, '/api/health')
      : '/api/health';
    url.search = '';
    url.hash = '';
    return url.toString();
  }

  function identityFromHealth(payload) {
    const identity = payload?.azure_host;
    if (
      !identity
      || identity.verified !== true
      || !identity.resource_group
      || !identity.vm_name
      || !identity.location
      || !SOURCE_REF_PATTERN.test(identity.source_ref || '')
    ) {
      return null;
    }
    return identity;
  }

  function renderHealth(payload, latencyMilliseconds) {
    const identity = identityFromHealth(payload);
    const apiReady = (
      payload?.schema_version === 'servicetracer.demo-api-health.v1'
      && payload.status === 'healthy'
      && payload.backend_target_configured === true
    );

    setText(elements.api, apiReady ? 'Healthy API response' : 'Health contract rejected');
    setText(elements.latency, `${Math.round(latencyMilliseconds)} ms`);
    setText(elements.checkedAt, formatClock());

    if (!apiReady) {
      setMonitorState('API health rejected', 'warning');
      setText(elements.scope, '', 'Not verified');
      setText(elements.vm, '', 'Not verified');
      setText(elements.location, '', 'Not verified');
      setText(elements.sourceRef, '', 'Not verified');
      return;
    }

    if (!identity) {
      setMonitorState('API healthy · Azure host identity unverified', 'warning');
      setText(elements.scope, '', 'Identity not returned');
      setText(elements.vm, '', 'Identity not returned');
      setText(elements.location, '', 'Identity not returned');
      setText(elements.sourceRef, '', 'Identity not returned');
      return;
    }

    setText(elements.scope, identity.resource_group);
    setText(elements.vm, identity.vm_name);
    setText(elements.location, identity.location);
    setText(elements.sourceRef, shortRef(identity.source_ref));
    setMonitorState('Frontend ↔ governed collector API live', 'healthy');
    elements.panel?.classList.remove('monitor-pulse');
    window.requestAnimationFrame(() => elements.panel?.classList.add('monitor-pulse'));
  }

  function renderHealthFailure(error) {
    console.warn('Live provenance monitor health check failed.', error);
    setMonitorState('Collector API monitor unavailable', 'warning');
    setText(elements.api, 'No accepted health response');
    setText(elements.latency, '', '—');
    setText(elements.checkedAt, formatClock());
  }

  async function pollHealth() {
    if (!monitor.healthUrl || monitor.polling) {
      return;
    }
    monitor.polling = true;
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), HEALTH_TIMEOUT_MS);
    const startedAt = performance.now();
    try {
      const response = await originalFetch(monitor.healthUrl, {
        cache: 'no-store',
        signal: controller.signal,
      });
      if (!response.ok) {
        throw new Error(`Health endpoint returned HTTP ${response.status}`);
      }
      renderHealth(await response.json(), performance.now() - startedAt);
    } catch (error) {
      renderHealthFailure(error);
    } finally {
      window.clearTimeout(timeout);
      monitor.polling = false;
    }
  }

  function renderTransactionStarted(requestId) {
    setText(elements.requestId, requestId);
    setText(elements.transaction, 'Request in flight');
    setMonitorState('Correlated frontend request in flight', 'neutral');
  }

  function renderTransactionResponse(payload, requestId, responseStatus) {
    const responseRequestId = payload?.request_id;
    if (responseRequestId !== requestId) {
      setText(elements.transaction, 'Request ID mismatch · evidence rejected');
      setMonitorState('Correlation proof rejected', 'warning');
      return;
    }
    const transactionCount = Array.isArray(payload?.transactions)
      ? payload.transactions.length
      : 0;
    setText(elements.transaction, `HTTP ${responseStatus} · ${transactionCount} transactions correlated`);
    setMonitorState('Frontend request correlated to collector response', 'healthy');
  }

  function renderTransactionFailure(error) {
    console.warn('Correlated frontend request failed.', error);
    setText(elements.transaction, 'Request failed before accepted correlation proof');
    setMonitorState('Correlated request failed', 'warning');
  }

  window.fetch = async (input, options = {}) => {
    const details = requestDetails(input, options);
    if (!isRunRequest(details)) {
      return originalFetch(input, options);
    }

    const requestId = makeRequestId();
    const headers = new Headers(
      options.headers || (input instanceof Request ? input.headers : undefined),
    );
    headers.set(REQUEST_HEADER, requestId);
    renderTransactionStarted(requestId);

    try {
      const response = await originalFetch(input, { ...options, headers });
      response.clone().json()
        .then((payload) => renderTransactionResponse(payload, requestId, response.status))
        .catch(renderTransactionFailure);
      return response;
    } catch (error) {
      renderTransactionFailure(error);
      throw error;
    }
  };

  async function initializeMonitor() {
    if (!elements.panel) {
      return;
    }
    setText(elements.browser, window.location.host || 'Local browser');
    try {
      const response = await originalFetch('report-source.json', { cache: 'no-store' });
      if (!response.ok) {
        throw new Error(`report-source.json returned HTTP ${response.status}`);
      }
      const config = await response.json();
      monitor.runUrl = config.live_demo_api_url || '';
      if (!monitor.runUrl) {
        throw new Error('No live demo API is configured');
      }
      monitor.healthUrl = deriveHealthUrl(monitor.runUrl);
      setText(elements.endpoint, new URL(monitor.runUrl).host);
      await pollHealth();
      monitor.timer = window.setInterval(pollHealth, HEALTH_INTERVAL_MS);
    } catch (error) {
      renderHealthFailure(error);
      setText(elements.endpoint, '', 'No endpoint configured');
    }
  }

  window.addEventListener('pagehide', () => {
    if (monitor.timer) {
      window.clearInterval(monitor.timer);
    }
  });

  initializeMonitor();
})();
