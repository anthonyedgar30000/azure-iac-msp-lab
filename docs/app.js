const state = {
  report: null,
  completedSteps: new Set(),
};

const elements = {
  runButton: document.querySelector('#run-analysis'),
  resetButton: document.querySelector('#reset-demo'),
  incidentChip: document.querySelector('#incident-chip'),
  evidenceSummary: document.querySelector('#evidence-summary'),
  loadBalancerNode: document.querySelector('#load-balancer-node'),
  loadBalancerState: document.querySelector('#load-balancer-state'),
  loadBalancerBadge: document.querySelector('#load-balancer-badge'),
  vpn01Node: document.querySelector('#vpn01-node'),
  vpn02Node: document.querySelector('#vpn02-node'),
  vpn01Rate: document.querySelector('#vpn01-rate'),
  vpn02Rate: document.querySelector('#vpn02-rate'),
  vpn01Badge: document.querySelector('#vpn01-badge'),
  vpn02Badge: document.querySelector('#vpn02-badge'),
  result: document.querySelector('#analysis-result'),
  findingText: document.querySelector('#finding-text'),
  factLoadBalancer: document.querySelector('#fact-load-balancer'),
  factSuspect: document.querySelector('#fact-suspect'),
  factHealthy: document.querySelector('#fact-healthy'),
  factRootCause: document.querySelector('#fact-root-cause'),
  boundaryBackend: document.querySelector('#boundary-backend'),
  boundaryStatement: document.querySelector('#boundary-statement'),
  workflowPanel: document.querySelector('#workflow-panel'),
  workflowList: document.querySelector('#workflow-list'),
  completionMessage: document.querySelector('#completion-message'),
};

function delay(milliseconds) {
  return new Promise((resolve) => window.setTimeout(resolve, milliseconds));
}

function asPercent(value) {
  if (typeof value !== 'number') {
    return '—';
  }
  return `${Math.round(value * 100)}%`;
}

function setNodeState(node, stateName) {
  node.classList.remove('node-pending', 'node-analyzing', 'node-healthy', 'node-failed');
  node.classList.add(`node-${stateName}`);
}

function setBadge(badge, text, healthy) {
  badge.textContent = text;
  badge.classList.remove('badge-neutral', 'badge-healthy', 'badge-failed');
  badge.classList.add(healthy ? 'badge-healthy' : 'badge-failed');
}

function renderWorkflow() {
  elements.workflowList.replaceChildren();

  state.report.technician_workflow.forEach((step) => {
    const item = document.createElement('li');
    item.className = 'workflow-item';
    item.dataset.stepId = step.step_id;

    const copy = document.createElement('div');
    copy.className = 'workflow-copy';

    const title = document.createElement('strong');
    title.textContent = step.action;

    const purpose = document.createElement('p');
    purpose.className = 'workflow-purpose';
    purpose.textContent = step.purpose;

    const button = document.createElement('button');
    button.className = 'workflow-button';
    button.type = 'button';
    button.textContent = 'Mark complete';
    button.addEventListener('click', () => completeWorkflowStep(item, button, step.step_id));

    copy.append(title, purpose);
    item.append(document.createElement('span'), copy, button);
    elements.workflowList.append(item);
  });
}

function completeWorkflowStep(item, button, stepId) {
  state.completedSteps.add(stepId);
  item.classList.add('is-complete');
  button.disabled = true;
  button.textContent = 'Completed';

  if (state.completedSteps.size === state.report.technician_workflow.length) {
    elements.completionMessage.classList.remove('is-hidden');
    elements.incidentChip.textContent = 'Service verified';
    elements.incidentChip.classList.remove('status-warning');
    elements.incidentChip.classList.add('status-neutral');
  }
}

function populateReport() {
  const report = state.report;
  const failureRates = report.localization.backend_failure_rates;
  const backendStates = report.load_balancer.backend_states;
  const incident = report.incident;

  elements.incidentChip.textContent = 'Technician investigation required';
  elements.incidentChip.classList.remove('status-neutral');
  elements.incidentChip.classList.add('status-warning');

  elements.evidenceSummary.textContent = `${incident.attempts} correlated transactions: ${incident.successful_attempts} successful, ${incident.failed_attempts} failed.`;
  elements.loadBalancerState.textContent = 'Healthy under configured probe';
  elements.loadBalancerBadge.textContent = `${report.load_balancer.probe_name} · ${report.load_balancer.probe_scope}`;
  elements.loadBalancerBadge.classList.remove('badge-neutral');
  elements.loadBalancerBadge.classList.add('badge-healthy');

  elements.vpn01Rate.textContent = asPercent(failureRates['VPN-01']);
  elements.vpn02Rate.textContent = asPercent(failureRates['VPN-02']);
  setBadge(elements.vpn01Badge, `Probe ${backendStates['VPN-01'].probe_status}`, true);
  setBadge(elements.vpn02Badge, `Probe ${backendStates['VPN-02'].probe_status}`, true);

  elements.findingText.textContent = report.service_tracer_finding;
  elements.factLoadBalancer.textContent = 'Healthy under configured probe';
  elements.factSuspect.textContent = report.localization.suspect_backend;
  elements.factHealthy.textContent = report.localization.healthy_comparison_backend;
  elements.factRootCause.textContent = 'Not determined by ServiceTracer';
  elements.boundaryBackend.textContent = report.investigation_boundary.service_tracer_stops_at;
  elements.boundaryStatement.textContent = report.investigation_boundary.statement;

  renderWorkflow();
  elements.result.classList.remove('is-hidden');
  elements.workflowPanel.classList.remove('is-hidden');
}

async function runAnalysis() {
  elements.runButton.disabled = true;
  elements.runButton.textContent = 'Analyzing evidence…';
  elements.incidentChip.textContent = 'Analysis running';
  elements.incidentChip.classList.remove('status-warning');
  elements.incidentChip.classList.add('status-neutral');

  setNodeState(elements.loadBalancerNode, 'analyzing');
  await delay(550);
  setNodeState(elements.loadBalancerNode, 'healthy');
  elements.loadBalancerState.textContent = 'Probe healthy';
  elements.loadBalancerBadge.textContent = 'Listener responds';
  elements.loadBalancerBadge.classList.remove('badge-neutral');
  elements.loadBalancerBadge.classList.add('badge-healthy');

  setNodeState(elements.vpn01Node, 'analyzing');
  setNodeState(elements.vpn02Node, 'analyzing');
  await delay(650);

  populateReport();
  setNodeState(elements.vpn01Node, 'healthy');
  setNodeState(elements.vpn02Node, 'failed');

  elements.runButton.textContent = 'Analysis complete';
  elements.result.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function resetDemo() {
  state.completedSteps.clear();
  elements.runButton.disabled = false;
  elements.runButton.textContent = 'Run incident analysis';
  elements.incidentChip.textContent = 'Awaiting analysis';
  elements.incidentChip.classList.remove('status-warning');
  elements.incidentChip.classList.add('status-neutral');
  elements.evidenceSummary.textContent = 'No evidence analyzed yet.';

  setNodeState(elements.loadBalancerNode, 'pending');
  setNodeState(elements.vpn01Node, 'pending');
  setNodeState(elements.vpn02Node, 'pending');

  elements.loadBalancerState.textContent = 'Not evaluated';
  elements.loadBalancerBadge.textContent = 'TCP 443 probe';
  elements.loadBalancerBadge.className = 'node-badge badge-neutral';
  elements.vpn01Rate.textContent = '—';
  elements.vpn02Rate.textContent = '—';
  elements.vpn01Badge.textContent = 'Probe unknown';
  elements.vpn02Badge.textContent = 'Probe unknown';
  elements.vpn01Badge.className = 'node-badge badge-neutral';
  elements.vpn02Badge.className = 'node-badge badge-neutral';

  elements.result.classList.add('is-hidden');
  elements.workflowPanel.classList.add('is-hidden');
  elements.completionMessage.classList.add('is-hidden');
  elements.workflowList.replaceChildren();
}

async function loadReport() {
  try {
    const response = await fetch('technician-handoff-report.json', { cache: 'no-store' });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    state.report = await response.json();
    elements.runButton.disabled = false;
  } catch (error) {
    console.error('Could not load demo report:', error);
    elements.runButton.disabled = true;
    elements.runButton.textContent = 'Report unavailable';
    elements.incidentChip.textContent = 'Demo data unavailable';
    elements.evidenceSummary.textContent = 'Serve this folder over HTTP, such as through GitHub Pages.';
  }
}

elements.runButton.disabled = true;
elements.runButton.addEventListener('click', runAnalysis);
elements.resetButton.addEventListener('click', resetDemo);
loadReport();
