(() => {
  const HEALTH_INTERVAL_MS = 15000;
  const HEALTH_TIMEOUT_MS = 6000;
  const SOURCE_REF_PATTERN = /^[0-9a-f]{40}$/;
  const originalFetch = window.fetch.bind(window);

  const monitor = {
    runUrl: '',
    healthUrl: '',
    expectedHost: null,
    timer: null,
    polling: false,
    healthAccepted: false,
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
    if (!elements.state) return;
    elements.state.textContent = label;
    elements.state.classList.remove(
      'monitor-state-neutral',
      'monitor-state-healthy',
      'monitor-state-warning',
    );
    elements.state.classList.add(`monitor-state-${stateName}`);
  }

  function setText(element, value, fallback = 'Not observed') {
    if (element) element.textContent = value || fallback;
  }

  function formatClock(value = new Date()) {
    return new Intl.DateTimeFormat(undefined, {
      hour: 'numeric',
      minute: '2-digit',
      second: '2-digit',
    }).format(value);
  }

  function shortRef(value) {
    return SOURCE_REF_PATTERN.test(value || '') ? value.slice(0, 12) : 'Not reported';
  }

  function requestDetails(input, options = {}) {
    const rawUrl = input instanceof Request ? input.url : input;
    const method = (
      options.method || (input instanceof Request ? input.method : 'GET') || 'GET'
    ).toUpperCase();
    return { url: new URL(rawUrl, window.location.href), method };
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

  function expectedHostFromConfig(config) {
    const expected = config?.expected_azure_host;
    const fields = ['resource_group', 'vm_name', 'location', 'hosting_model'];
    if (!expected || fields.some((field) => typeof expected[field] !== 'string' || !expected[field].trim())) {
      return null;
    }
    return Object.fromEntries(fields.map((field) => [field, expected[field].trim()]));
  }

  function verifiedRuntimeIdentity(payload) {
    const identity = payload?.azure_host;
    const expected = monitor.expectedHost;
    if (
      !expected
      || !identity
      || identity.verified !== true
      || identity.resource_group !== expected.resource_group
      || identity.vm_name !== expected.vm_name
      || identity.location !== expected.location
      || payload.hosting_model !== expected.hosting_model
    ) {
      return null;
    }
    return identity;
  }

  function renderConfiguredDeployment() {
    const expected = monitor.expectedHost;
    if (!expected) return;
    setText(elements.scope, expected.resource_group);
    setText(elements.vm, expected.vm_name);
    setText(elements.location, expected.location);
    setText(elements.sourceRef, '', 'Runtime source ref not reported');
  }

  function updateStaticCopy() {
    const title = document.querySelector('#live-monitor-title');
    if (title) title.textContent = 'Frontend-to-API path';

    const headingQuiet = document.querySelector('.live-monitor-heading .quiet');
    if (headingQuiet) {
      headingQuiet.textContent = 'The resource group is the configured Azure deployment scope. Traffic terminates at the dedicated ServiceTracer demo API VM.';
    }

    const fieldLabels = document.querySelectorAll('.monitor-field span');
    fieldLabels.forEach((label) => {
      if (label.textContent.trim() === 'Collector VM') label.textContent = 'API VM';
    });

    const hostingValue = Array.from(document.querySelectorAll('.monitor-field strong'))
      .find((node) => node.textContent.trim() === 'collector_vm_systemd');
    if (hostingValue) hostingValue.textContent = 'dedicated_vm_subproject';

    const architectureState = document.querySelector('.architecture-state');
    if (architectureState) architectureState.textContent = 'Current independent VM deployment';

    const replacements = new Map([
      ['Frontend-to-collector path', 'Frontend-to-API path'],
      ['Current collector-hosted golden path', 'Current independent VM deployment'],
      ['Private collector', 'Dedicated API VM'],
      ['vm-stcollector-mst-dev · 10.20.40.10', 'vm-st-demo-api-mst-dev'],
      ['lb-st-demo-api-mst-dev', 'Public IP → dedicated API VM'],
      ['The collector has no directly attached public IP. NSG rules admit only the required web path from the public ingress.', 'The dedicated API VM is reached through its governed public endpoint. NSG rules admit only the required web path.'],
      ['Forwards TCP 80/443 to the private collector. The load balancer does not inspect the application request or terminate TLS.', 'Routes HTTPS traffic to the dedicated API VM through the governed public endpoint.'],
      ['The dedicated public load balancer forwards TCP 443 to the private collector.', 'The governed public endpoint forwards HTTPS traffic to the dedicated API VM.'],
      ['The resource group is shown as the governed Azure scope. Traffic terminates at the API process on the collector VM.', 'The resource group is shown as the configured Azure scope. Traffic terminates at the API process on the dedicated VM.'],
    ]);

    document.querySelectorAll('strong, span, p, h2, h3').forEach((node) => {
      const replacement = replacements.get(node.textContent.trim());
      if (replacement) node.textContent = replacement;
    });
  }

  function renderHealth(payload, latencyMilliseconds) {
    const apiReady = (
      payload?.schema_version === 'servicetracer.demo-api-health.v1'
      && payload.status === 'healthy'
      && payload.backend_target_configured === true
    );
    monitor.healthAccepted = apiReady;

    setText(elements.api, apiReady ? 'Health endpoint reachable' : 'Health contract rejected');
    setText(elements.latency, `${Math.round(latencyMilliseconds)} ms`);
    setText(elements.checkedAt, formatClock());

    if (!apiReady) {
      setMonitorState('API health rejected', 'warning');
      return;
    }

    const identity = verifiedRuntimeIdentity(payload);
    if (identity) {
      setText(elements.scope, identity.resource_group);
      setText(elements.vm, identity.vm_name);
      setText(elements.location, identity.location);
      setText(elements.sourceRef, shortRef(identity.source_ref));
      setMonitorState('API healthy · Azure runtime identity verified', 'healthy');
    } else {
      renderConfiguredDeployment();
      const reason = payload?.azure_host?.reason || 'runtime metadata unavailable';
      setMonitorState(`API healthy · Azure runtime identity unverified (${reason})`, 'warning');
    }

    elements.panel?.classList.remove('monitor-pulse');
    window.requestAnimationFrame(() => elements.panel?.classList.add('monitor-pulse'));
  }

  function renderHealthFailure(error) {
    monitor.healthAccepted = false;
    console.warn('Live API health check failed.', error);
    setMonitorState('Live API monitor unavailable', 'warning');
    setText(elements.api, 'No accepted health response');
    setText(elements.latency, '', '—');
    setText(elements.checkedAt, formatClock());
  }

  async function pollHealth() {
    if (!monitor.healthUrl || monitor.polling) return;
    monitor.polling = true;
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), HEALTH_TIMEOUT_MS);
    const startedAt = performance.now();
    try {
      const response = await originalFetch(monitor.healthUrl, {
        cache: 'no-store',
        signal: controller.signal,
      });
      if (!response.ok) throw new Error(`Health endpoint returned HTTP ${response.status}`);
      renderHealth(await response.json(), performance.now() - startedAt);
    } catch (error) {
      renderHealthFailure(error);
    } finally {
      window.clearTimeout(timeout);
      monitor.polling = false;
    }
  }

  function renderTransactionStarted() {
    setText(elements.requestId, '', 'Awaiting API-assigned request ID');
    setText(elements.transaction, 'Request in flight');
    setMonitorState('Live API request in flight', 'neutral');
  }

  function renderTransactionResponse(payload, responseStatus) {
    const requestId = payload?.request_id || null;
    const validPayload = (
      responseStatus === 200
      && payload?.schema_version === 'servicetracer.demo-api-response.v1'
      && requestId
      && Array.isArray(payload?.transactions)
    );

    if (!validPayload) {
      setText(elements.transaction, 'Response contract rejected');
      setMonitorState('Live API response rejected', 'warning');
      return;
    }

    setText(elements.requestId, requestId);
    const transactionCount = payload.transactions.length;
    setText(elements.transaction, `HTTP ${responseStatus} · API request ${requestId} · ${transactionCount} transactions correlated`);

    if (verifiedRuntimeIdentity(payload)) {
      setMonitorState('Live API transaction and Azure runtime identity verified', 'healthy');
    } else {
      setMonitorState('Live API transaction verified · Azure runtime identity remains unverified', 'warning');
    }
  }

  function renderTransactionFailure(error) {
    console.warn('Live API request failed.', error);
    setText(elements.transaction, 'Request failed before an accepted API response');
    setMonitorState('Live API request failed', 'warning');
  }

  window.fetch = async (input, options = {}) => {
    const details = requestDetails(input, options);
    if (!isRunRequest(details)) return originalFetch(input, options);

    renderTransactionStarted();
    try {
      // Do not add the legacy collector correlation header. The independent API
      // assigns and returns its own request_id, avoiding an unnecessary CORS header.
      const response = await originalFetch(input, options);
      response.clone().json()
        .then((payload) => renderTransactionResponse(payload, response.status))
        .catch(renderTransactionFailure);
      return response;
    } catch (error) {
      renderTransactionFailure(error);
      throw error;
    }
  };

  async function initializeMonitor() {
    if (!elements.panel) return;
    updateStaticCopy();
    setText(elements.browser, window.location.host || 'Local browser');
    try {
      const response = await originalFetch('report-source.json', { cache: 'no-store' });
      if (!response.ok) throw new Error(`report-source.json returned HTTP ${response.status}`);
      const config = await response.json();
      monitor.runUrl = config.live_demo_api_url || '';
      monitor.expectedHost = expectedHostFromConfig(config);
      if (!monitor.runUrl) throw new Error('No live demo API is configured');
      if (!monitor.expectedHost) throw new Error('No configured Azure deployment identity is available');
      monitor.healthUrl = deriveHealthUrl(monitor.runUrl);
      setText(elements.endpoint, new URL(monitor.runUrl).host);
      renderConfiguredDeployment();
      await pollHealth();
      monitor.timer = window.setInterval(pollHealth, HEALTH_INTERVAL_MS);
    } catch (error) {
      renderHealthFailure(error);
      setText(elements.endpoint, '', 'No governed endpoint configured');
    }
  }

  window.addEventListener('pagehide', () => {
    if (monitor.timer) window.clearInterval(monitor.timer);
  });

  initializeMonitor();
})();
