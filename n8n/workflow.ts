import { workflow, node, trigger, sticky, newCredential, splitInBatches, nextBatch, expr } from '@n8n/workflow-sdk';

const dailyTrigger = trigger({
  type: 'n8n-nodes-base.scheduleTrigger',
  version: 1.3,
  config: {
    name: 'Daily 07:00 Discovery Run',
    position: [-620, 300],
    parameters: {
      rule: {
        interval: [{ field: 'days', daysInterval: 1, triggerAtHour: 7, triggerAtMinute: 0 }]
      }
    }
  },
  output: [{}]
});

const buildSeeds = node({
  type: 'n8n-nodes-base.code',
  version: 2,
  config: {
    name: 'Build Intent Seed Queries',
    position: [-400, 300],
    parameters: {
      mode: 'runOnceForAllItems',
      language: 'javaScript',
      jsCode: `
const NEGATIVES = '-CRO -CDMO -"contract research" -diagnostic -reagent -"research use only" -supplier -catalog -"market report"';

const BLOCKED = [
  'indeed.com','ziprecruiter.com','glassdoor.com','jooble.org','simplyhired.com',
  'marketresearch.com','grandviewresearch.com','marketsandmarkets.com',
  'researchandmarkets.com','prweb.com','medium.com','quora.com'
];

const SEEDS = [
  { seed_id: 'CAP-01', query: '"Series A" antibody pipeline biotech financing', signal_type: 'capital', days: 30 },
  { seed_id: 'CAP-02', query: 'seed financing "protein engineering" therapeutics startup', signal_type: 'capital', days: 45 },
  { seed_id: 'CAP-03', query: 'biotech raises funding "bispecific antibody" preclinical', signal_type: 'capital', days: 30 },
  { seed_id: 'CAP-04', query: 'financing "advance our antibody pipeline" biotech', signal_type: 'capital', days: 60 },
  { seed_id: 'CAP-05', query: 'startup emerges from stealth antibody discovery funding', signal_type: 'capital', days: 60 },
  { seed_id: 'PRG-01', query: '"development candidate" nomination antibody biotech', signal_type: 'milestone', days: 30 },
  { seed_id: 'PRG-02', query: '"lead optimization" therapeutic antibody company program', signal_type: 'program', days: 45 },
  { seed_id: 'PRG-03', query: '"pipeline expansion" bispecific antibody biotech', signal_type: 'program', days: 45 },
  { seed_id: 'PRG-04', query: '"new antibody program" preclinical biotech target', signal_type: 'program', days: 45 },
  { seed_id: 'PRG-05', query: 'biotech "IND-enabling" antibody candidate announcement', signal_type: 'milestone', days: 45 },
  { seed_id: 'JOB-01', query: '"Head of Antibody Discovery" hiring biotech careers', signal_type: 'hiring', days: 30 },
  { seed_id: 'JOB-02', query: '"Director, Protein Engineering" biotech job therapeutics', signal_type: 'hiring', days: 30 },
  { seed_id: 'JOB-03', query: '"computational protein design" scientist job biotech', signal_type: 'hiring', days: 30 },
  { seed_id: 'JOB-04', query: '"antibody developability" scientist hiring biotech', signal_type: 'hiring', days: 45 },
  { seed_id: 'JOB-05', query: '"bispecific antibody" engineer job preclinical company', signal_type: 'hiring', days: 45 },
  { seed_id: 'SCI-01', query: '"affinity maturation" therapeutic antibody company publication', signal_type: 'scientific', days: 90 },
  { seed_id: 'SCI-02', query: '"antibody humanization" therapeutic candidate company', signal_type: 'scientific', days: 90 },
  { seed_id: 'SCI-03', query: 'membrane protein GPCR therapeutic antibody discovery company', signal_type: 'scientific', days: 90 },
  { seed_id: 'SCI-04', query: 'antibody developability aggregation therapeutic company study', signal_type: 'scientific', days: 90 },
  { seed_id: 'EXE-01', query: 'biotech partners wet-lab validation antibody discovery collaboration', signal_type: 'execution', days: 60 },
  { seed_id: 'EXE-02', query: 'biotech builds antibody discovery capability platform in-house', signal_type: 'execution', days: 60 }
];

return SEEDS.map(s => ({
  json: {
    seed_id: s.seed_id,
    query: s.query,
    signal_type: s.signal_type,
    days: s.days,
    max_results: 12,
    search_query: s.query + ' ' + NEGATIVES,
    topic: (s.signal_type === 'capital' || s.signal_type === 'milestone') ? 'news' : 'general',
    exclude_domains: BLOCKED
  }
}));
`
    }
  },
  output: [{ seed_id: 'CAP-01', query: '"Series A" antibody pipeline biotech financing', signal_type: 'capital', days: 30, max_results: 12, search_query: '"Series A" antibody pipeline biotech financing -CRO -CDMO', topic: 'news', exclude_domains: ['indeed.com'] }]
});

const loopSeeds = splitInBatches({
  version: 3,
  config: { name: 'Loop Over Seeds', position: [-180, 300], parameters: { batchSize: 1 } }
});

const tavilySearch = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Tavily Search',
    position: [60, 460],
    onError: 'continueRegularOutput',
    retryOnFail: true,
    maxTries: 3,
    waitBetweenTries: 3000,
    parameters: {
      method: 'POST',
      url: 'https://api.tavily.com/search',
      authentication: 'genericCredentialType',
      genericAuthType: 'httpBearerAuth',
      sendBody: true,
      contentType: 'json',
      specifyBody: 'json',
      jsonBody: expr('{{ JSON.stringify({ query: $json.search_query, search_depth: "basic", topic: $json.topic, days: $json.days, max_results: $json.max_results, include_answer: false, include_raw_content: false, exclude_domains: $json.exclude_domains }) }}'),
      options: { timeout: 60000 }
    },
    credentials: { httpBearerAuth: newCredential('Tavily API') }
  },
  output: [{ query: 'antibody', results: [{ title: 'NovaBinder raises $42M Series A', url: 'https://novabinder.com/news/series-a', content: 'The Series A will fund lead optimization of our preclinical bispecific program.', score: 0.82, published_date: 'Thu, 09 Jul 2026 12:02:17 GMT' }] }]
});

const collectResults = node({
  type: 'n8n-nodes-base.code',
  version: 2,
  config: {
    name: 'Attach Seed Metadata',
    position: [280, 460],
    parameters: {
      mode: 'runOnceForAllItems',
      language: 'javaScript',
      jsCode: `
const seed = $('Loop Over Seeds').first().json;
const out = [];

for (const item of $input.all()) {
  const results = item.json.results || [];
  for (const r of results) {
    out.push({
      json: {
        seed_id: seed.seed_id,
        query: seed.query,
        signal_type: seed.signal_type,
        date_window_days: seed.days,
        source_url: r.url || '',
        title: r.title || '',
        snippet: r.content || '',
        raw_text: r.raw_content || '',
        published_raw: r.published_date || '',
        tavily_score: r.score || 0
      }
    });
  }
}

return out;
`
    }
  },
  output: [{ seed_id: 'CAP-01', query: '"Series A" antibody pipeline biotech financing', signal_type: 'capital', date_window_days: 30, source_url: 'https://novabinder.com/news/series-a', title: 'NovaBinder raises $42M Series A', snippet: 'The Series A will fund lead optimization.', raw_text: '', published_raw: 'Thu, 09 Jul 2026 12:02:17 GMT', tavily_score: 0.82 }]
});

const gatePassOne = node({
  type: 'n8n-nodes-base.code',
  version: 2,
  config: {
    name: 'Resolve, Exclude and Score',
    position: [60, 140],
    parameters: {
      mode: 'runOnceForAllItems',
      language: 'javaScript',
      jsCode: `
const NON_COMPANY = ['linkedin.com','pubmed.ncbi.nlm.nih.gov','ncbi.nlm.nih.gov','clinicaltrials.gov','reporter.nih.gov','patents.google.com','sec.gov','crunchbase.com','pitchbook.com','dealroom.co','europepmc.org','biorxiv.org','medrxiv.org','nature.com','sciencedirect.com','wikipedia.org','x.com','twitter.com','youtube.com','reddit.com','stocktitan.net','businessinsider.com','ft.com'];

const MEDIA_RX = /(news|press|wire|journal|daily|times|post|herald|report|magazine|media|blog|today|insider|weekly|review|pharmaphorum|biospace|endpts|fierce|labiotech|statnews|scrip|genengnews|biotechniques)/i;

const COMPETITORS = ['absci.com','generatebiomedicines.com','biolojic.com','nabla.bio','chai-discovery.com','cradle.bio','diffusebio.com','abcellera.com','adaptyvbio.com','exscientia.ai','profluent.bio','latentlabs.com'];

const EXCL = {
  cro_cdmo: ['contract research organization','contract development and manufacturing','contract manufacturing','fee-for-service','our services include','outsourcing partner','custom antibody production'],
  diagnostics_reagent: ['research use only','diagnostic assay','test kit','catalog antibody','catalogue antibody','elisa kit'],
  academic_only: ['department of','school of medicine','university','college of'],
  non_buyer: ['venture capital','consulting services','accelerator program','market report','industry report','staffing agency','recruitment agency'],
  competitor: ['ai-powered antibody design platform','generative protein design platform','protein language model platform','in silico antibody design services']
};

const SELF_REF = ['we are a','we provide','our clients','our customers','our services','is a leading','as a global','capabilities include'];

const MODALITY_OK = ['monoclonal antibody','bispecific','multispecific','trispecific','nanobody','vhh','scfv','fab fragment','antibody fragment','engineered protein','therapeutic binder','antibody therapeutic'];
const MODALITY_COND = ['antibody-drug conjugate','fusion protein','cytokine engineering','fc fusion','car-t','cell therapy'];
const MODALITY_BAD = ['small molecule','gene therapy','aav vector','mrna vaccine','sirna','antisense oligonucleotide','crispr editing','microbiome'];

const BOTTLENECKS = {
  discovery: ['difficult target','undruggable','hit rate','binder diversity','de novo','gpcr','membrane protein','ion channel'],
  binding_performance: ['affinity maturation','picomolar','potency','epitope coverage','arm balancing','avidity'],
  specificity: ['cross-reactivity','off-target','selectivity','polyreactivity'],
  sequence_risk: ['humanization','immunogenicity','sequence liabilit','aggregation','thermostability'],
  development_risk: ['developability','expression titer','solubility','manufacturability','viscosity'],
  decision_risk: ['candidate selection','shortlist','wet-lab capacity','prioritize variants','screening throughput']
};

const STAGES = {
  discovery: ['discovery stage','hit identification','binder generation'],
  lead_optimization: ['lead optimization','lead series','optimization campaign'],
  candidate_selection: ['development candidate','candidate nomination','candidate selection'],
  preclinical: ['preclinical','ind-enabling','ind enabling'],
  clinical: ['phase 1','phase 2','phase 3','first-in-human']
};

const FUNDING = ['series a','series b','seed round','seed financing','oversubscribed','raises $','raised $','million financing','sbir','sttr','non-dilutive'];

const STRENGTH = { capital: 1.0, milestone: 0.95, program: 0.9, hiring: 0.8, execution: 0.7, scientific: 0.6 };

function hits(text, terms) {
  const found = [];
  for (const t of terms) { if (text.indexOf(t) !== -1) found.push(t); }
  return found;
}

function domainOf(url) {
  try {
    let h = new URL(url).hostname.toLowerCase();
    return h.startsWith('www.') ? h.slice(4) : h;
  } catch (e) { return ''; }
}

function parseDate(raw) {
  if (!raw) return null;
  const d = new Date(raw);
  if (!isNaN(d.getTime())) return d.toISOString().slice(0, 10);
  const m = String(raw).match(/(20\\d{2})-(\\d{2})-(\\d{2})/);
  return m ? m[0] : null;
}

function canonical(name) {
  let n = String(name || '').replace(/\\s+/g, ' ').trim();
  n = n.replace(/^.*?\\b(?:firm|biotech|startup|company|maker|developer|specialist|group)\\s+(?=[A-Z])/, '');
  n = n.replace(/[,\\s]+(inc|llc|ltd|limited|corp|corporation|co|plc|gmbh|ab|sa|nv|bv|pte|pty)\\.?$/i, '');
  const stripped = n.replace(/[,\\s]+(therapeutics|biosciences|bioscience|pharmaceuticals|pharma|labs|laboratories)\\.?$/i, '').trim();
  if (stripped.length >= 4) n = stripped;
  return n.trim();
}

function domainMatchesContent(domain, title, snippet) {
  let core = domain.split('.')[0];
  if (['www','news','markets','ir','investors','blog'].indexOf(core) !== -1) {
    const parts = domain.split('.');
    core = parts.length > 2 ? parts[1] : core;
  }
  const token = core.toLowerCase().replace(/[^a-z0-9]/g, '');
  if (token.length < 4) return false;
  const head = String(title || '').split(/\\s+[-|\\u2013\\u2014]\\s+/)[0];
  const hay = (head + ' ' + String(snippet || '').slice(0, 500)).toLowerCase().replace(/[^a-z0-9]/g, '');
  return hay.indexOf(token) !== -1;
}

const TITLE_RX = /^([A-Z][\\w&'\\-\\.]*(?:\\s+[A-Z][\\w&'\\-\\.]*){0,3}?)\\s+(?:raises|raised|announces|announced|launches|launched|secures|secured|closes|closed|nominates|nominated|unveils|expands|appoints|doses|reports|emerges|lands|nets|banks|debuts|adds|reels in)\\b/i;

const seen = {};
const out = [];

for (const item of $input.all()) {
  const j = item.json;
  const url = j.source_url || '';
  if (!url) continue;

  const signalDate = parseDate(j.published_raw);
  const key = url + '|' + (signalDate || '');
  if (seen[key]) continue;
  seen[key] = true;

  const domain = domainOf(url);
  const isPublisher = NON_COMPANY.indexOf(domain) !== -1 || MEDIA_RX.test(domain);

  let companyDomain = '';
  let companyName = '';
  let resolutionNote = '';

  if (domain && !isPublisher && domainMatchesContent(domain, j.title, j.snippet)) {
    companyDomain = domain;
    companyName = canonical(domain.split('.')[0].replace(/-/g, ' ').replace(/\\b\\w/g, c => c.toUpperCase()));
    resolutionNote = 'resolved from source domain';
  } else {
    const head = String(j.title || '').replace(/^.*?\\b(?:firm|biotech|startup|company|maker|developer|specialist|group)\\s+(?=[A-Z])/, '').trim();
    const m = head.match(TITLE_RX);
    if (m) {
      companyName = canonical(m[1]);
      resolutionNote = 'name parsed from headline; domain unverified';
    } else {
      resolutionNote = 'unresolved';
    }
  }

  const text = ((j.title || '') + ' ' + (j.snippet || '') + ' ' + (j.raw_text || '')).toLowerCase();

  let excluded = false;
  let exclusionReason = '';

  if (companyDomain && COMPETITORS.indexOf(companyDomain) !== -1) {
    excluded = true;
    exclusionReason = 'competitor: known AI antibody design provider';
  }

  if (!excluded) {
    for (const cat of Object.keys(EXCL)) {
      const h = hits(text, EXCL[cat]);
      if (h.length === 0) continue;
      if (cat === 'academic_only') {
        const commercial = hits(text, ['our pipeline','series a','series b','seed round','biotech company','spinout','spin-out']);
        if (commercial.length > 0 || companyDomain) continue;
      }
      excluded = true;
      exclusionReason = cat + ': ' + h.slice(0, 2).join(', ');
      break;
    }
  }

  if (!excluded) {
    const bare = /\\bcro\\b|\\bcdmo\\b|contract manufacturer/i;
    if (bare.test(text)) {
      const inTitle = bare.test(String(j.title || ''));
      const selfRef = hits(text, SELF_REF).length > 0;
      if (inTitle || selfRef) {
        excluded = true;
        exclusionReason = 'cro_cdmo: service provider is the subject';
      }
    }
  }

  const modOk = hits(text, MODALITY_OK);
  const modCond = hits(text, MODALITY_COND);
  const modBad = hits(text, MODALITY_BAD);

  const bottlenecks = [];
  for (const fam of Object.keys(BOTTLENECKS)) {
    if (hits(text, BOTTLENECKS[fam]).length > 0) bottlenecks.push(fam);
  }

  const stages = [];
  for (const st of Object.keys(STAGES)) {
    if (hits(text, STAGES[st]).length > 0) stages.push(st);
  }

  const funding = hits(text, FUNDING);

  let recency = 0.5;
  if (signalDate) {
    const days = Math.floor((Date.now() - new Date(signalDate).getTime()) / 86400000);
    if (days <= 14) recency = 1.0;
    else if (days <= 30) recency = 0.9;
    else if (days <= 60) recency = 0.7;
    else if (days <= 120) recency = 0.45;
    else if (days <= 180) recency = 0.25;
    else recency = 0.1;
  }

  const failed = [];
  const passed = [];
  let question = '';

  let fit = 0;
  if (modOk.length > 0) { fit += 12; passed.push('G1 modality'); }
  else if (modCond.length > 0) { fit += 6; question = 'confirm binder engineering is central to this modality'; }
  else { failed.push('G1 modality: no supported antibody/protein modality'); }
  if (modBad.length > 0 && modOk.length === 0) failed.push('G1 modality: excluded modality');

  const early = ['discovery','lead_optimization','candidate_selection','preclinical'];
  const hasEarly = stages.some(s => early.indexOf(s) !== -1);
  if (hasEarly) { fit += 7; passed.push('G2 stage'); }
  else if (stages.indexOf('clinical') !== -1) { question = question || 'confirm a parallel discovery program exists'; }
  else { failed.push('G2 stage: program stage not visible'); }

  if (bottlenecks.length > 0) { fit += Math.min(6, 3 * bottlenecks.length); passed.push('G3 bottleneck'); }
  else { failed.push('G3 bottleneck: no platform-addressable problem visible'); }

  const intent = Math.round(25 * (STRENGTH[j.signal_type] || 0.5) * recency);
  if (intent >= 12) passed.push('G4 timing trigger'); else failed.push('G4 timing: trigger weak or stale');

  let clarity = 0;
  if (bottlenecks.length > 0) clarity += 10;
  if (modOk.length > 0) clarity += 5;
  if (hasEarly) clarity += 5;
  if (clarity >= 15) passed.push('G5 project clarity'); else failed.push('G5 project: work package cannot be scoped');

  let budget = 0;
  if (funding.length > 0) budget += 9;
  if (j.signal_type === 'hiring') budget += 4;
  if (j.signal_type === 'capital' || j.signal_type === 'milestone') budget += 3;
  budget = Math.min(budget, 15);

  const buyer = companyDomain ? 6 : 3;
  let confidence = companyDomain ? 5 : 3;
  if (!companyDomain) confidence = Math.max(1, confidence - 2);

  const score = Math.min(fit, 25) + intent + Math.min(clarity, 20) + budget + buyer + confidence;

  out.push({
    json: {
      seed_id: j.seed_id,
      query: j.query,
      signal_type: j.signal_type,
      source_url: url,
      source_domain: domain,
      title: j.title,
      snippet: j.snippet,
      raw_text: j.raw_text,
      signal_date: signalDate,
      company_candidate: companyName,
      company_domain: companyDomain,
      resolution_note: resolutionNote,
      excluded: excluded,
      exclusion_reason: exclusionReason,
      score: excluded ? 0 : score,
      modality_evidence: modOk.join('; '),
      bottlenecks: bottlenecks.join('; '),
      stages: stages.join('; '),
      passed_gates: passed.join('; '),
      failed_gates: failed.join('; '),
      open_question: question,
      collected_at: new Date().toISOString().slice(0, 10)
    }
  });
}

return out;
`
    }
  },
  output: [{ seed_id: 'CAP-01', source_url: 'https://novabinder.com/news/series-a', company_candidate: 'NovaBinder', company_domain: 'novabinder.com', signal_date: '2026-07-09', excluded: false, exclusion_reason: '', score: 78, bottlenecks: 'binding_performance', stages: 'lead_optimization', open_question: '', title: 'NovaBinder raises $42M Series A' }]
});

const filterSurvivors = node({
  type: 'n8n-nodes-base.filter',
  version: 2.3,
  config: {
    name: 'Survived Hard Exclusions',
    position: [280, 140],
    parameters: {
      conditions: {
        options: { caseSensitive: true, leftValue: '', typeValidation: 'loose', version: 2 },
        conditions: [
          { id: 'not-excluded', leftValue: expr('{{ $json.excluded }}'), operator: { type: 'boolean', operation: 'false' }, rightValue: '' },
          { id: 'score-floor', leftValue: expr('{{ $json.score }}'), operator: { type: 'number', operation: 'gte' }, rightValue: 25 }
        ],
        combinator: 'and'
      },
      looseTypeValidation: true
    }
  },
  output: [{ source_url: 'https://novabinder.com/news/series-a', company_candidate: 'NovaBinder', score: 78, excluded: false }]
});

const loopSignals = splitInBatches({
  version: 3,
  config: { name: 'Loop Over Surviving Signals', position: [500, 140], parameters: { batchSize: 1 } }
});

const tavilyExtract = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Tavily Extract Full Page',
    position: [720, 300],
    onError: 'continueRegularOutput',
    retryOnFail: true,
    maxTries: 2,
    waitBetweenTries: 2000,
    parameters: {
      method: 'POST',
      url: 'https://api.tavily.com/extract',
      authentication: 'genericCredentialType',
      genericAuthType: 'httpBearerAuth',
      sendBody: true,
      contentType: 'json',
      specifyBody: 'json',
      jsonBody: expr('{{ JSON.stringify({ urls: [$json.source_url] }) }}'),
      options: { timeout: 60000, response: { response: { neverError: true } } }
    },
    credentials: { httpBearerAuth: newCredential('Tavily API') }
  },
  output: [{ results: [{ url: 'https://novabinder.com/news/series-a', raw_content: 'Full press release text about lead optimization, affinity maturation and developability risk.' }], failed_results: [] }]
});

const mergeFullText = node({
  type: 'n8n-nodes-base.code',
  version: 2,
  config: {
    name: 'Merge Page Text Into Signal',
    position: [940, 300],
    parameters: {
      mode: 'runOnceForAllItems',
      language: 'javaScript',
      jsCode: `
const signal = $('Loop Over Surviving Signals').first().json;
let fullText = '';

for (const item of $input.all()) {
  const results = item.json.results || [];
  for (const r of results) {
    if (r.raw_content && r.raw_content.length > fullText.length) fullText = r.raw_content;
  }
}

const enriched = Object.assign({}, signal);
if (fullText.length > (signal.raw_text || '').length) {
  enriched.raw_text = fullText.slice(0, 20000);
  enriched.text_enriched = true;
} else {
  enriched.text_enriched = false;
}

return [{ json: enriched }];
`
    }
  },
  output: [{ source_url: 'https://novabinder.com/news/series-a', company_candidate: 'NovaBinder', raw_text: 'Full press release text about lead optimization.', text_enriched: true }]
});

const buildCompanyMaster = node({
  type: 'n8n-nodes-base.code',
  version: 2,
  config: {
    name: 'Rescore and Build Company Master',
    position: [720, -20],
    parameters: {
      mode: 'runOnceForAllItems',
      language: 'javaScript',
      jsCode: `
const MODALITY_OK = ['monoclonal antibody','bispecific','multispecific','trispecific','nanobody','vhh','scfv','fab fragment','antibody fragment','engineered protein','therapeutic binder','antibody therapeutic'];
const MODALITY_COND = ['antibody-drug conjugate','fusion protein','cytokine engineering','fc fusion','car-t','cell therapy'];

const BOTTLENECKS = {
  discovery: ['difficult target','undruggable','hit rate','binder diversity','de novo','gpcr','membrane protein','ion channel'],
  binding_performance: ['affinity maturation','picomolar','potency','epitope coverage','arm balancing','avidity'],
  specificity: ['cross-reactivity','off-target','selectivity','polyreactivity'],
  sequence_risk: ['humanization','immunogenicity','sequence liabilit','aggregation','thermostability'],
  development_risk: ['developability','expression titer','solubility','manufacturability','viscosity'],
  decision_risk: ['candidate selection','shortlist','wet-lab capacity','prioritize variants','screening throughput']
};

const STAGES = {
  discovery: ['discovery stage','hit identification','binder generation'],
  lead_optimization: ['lead optimization','lead series','optimization campaign'],
  candidate_selection: ['development candidate','candidate nomination','candidate selection'],
  preclinical: ['preclinical','ind-enabling','ind enabling'],
  clinical: ['phase 1','phase 2','phase 3','first-in-human']
};

const FUNDING = ['series a','series b','seed round','seed financing','oversubscribed','raises $','raised $','million financing','sbir','sttr','non-dilutive'];
const STRENGTH = { capital: 1.0, milestone: 0.95, program: 0.9, hiring: 0.8, execution: 0.7, scientific: 0.6 };

function hits(text, terms) {
  const found = [];
  for (const t of terms) { if (text.indexOf(t) !== -1) found.push(t); }
  return found;
}

const scored = [];

for (const item of $input.all()) {
  const j = item.json;
  const text = ((j.title || '') + ' ' + (j.snippet || '') + ' ' + (j.raw_text || '')).toLowerCase();

  const modOk = hits(text, MODALITY_OK);
  const modCond = hits(text, MODALITY_COND);

  const bottlenecks = [];
  for (const fam of Object.keys(BOTTLENECKS)) {
    if (hits(text, BOTTLENECKS[fam]).length > 0) bottlenecks.push(fam);
  }

  const stages = [];
  for (const st of Object.keys(STAGES)) {
    if (hits(text, STAGES[st]).length > 0) stages.push(st);
  }

  const funding = hits(text, FUNDING);

  let recency = 0.5;
  if (j.signal_date) {
    const days = Math.floor((Date.now() - new Date(j.signal_date).getTime()) / 86400000);
    if (days <= 14) recency = 1.0;
    else if (days <= 30) recency = 0.9;
    else if (days <= 60) recency = 0.7;
    else if (days <= 120) recency = 0.45;
    else if (days <= 180) recency = 0.25;
    else recency = 0.1;
  }

  const failed = [];
  let question = j.open_question || '';

  let fit = 0;
  if (modOk.length > 0) fit += 12;
  else if (modCond.length > 0) fit += 6;
  else failed.push('G1 modality');

  const early = ['discovery','lead_optimization','candidate_selection','preclinical'];
  const hasEarly = stages.some(s => early.indexOf(s) !== -1);
  if (hasEarly) fit += 7; else failed.push('G2 stage');

  if (bottlenecks.length > 0) fit += Math.min(6, 3 * bottlenecks.length); else failed.push('G3 bottleneck');

  const intent = Math.round(25 * (STRENGTH[j.signal_type] || 0.5) * recency);
  if (intent < 12) failed.push('G4 timing');

  let clarity = 0;
  if (bottlenecks.length > 0) clarity += 10;
  if (modOk.length > 0) clarity += 5;
  if (hasEarly) clarity += 5;
  if (clarity < 15) failed.push('G5 project clarity');

  let budget = 0;
  if (funding.length > 0) budget += 9;
  if (j.signal_type === 'hiring') budget += 4;
  if (j.signal_type === 'capital' || j.signal_type === 'milestone') budget += 3;
  budget = Math.min(budget, 15);

  const buyer = j.company_domain ? 6 : 3;
  const confidence = j.company_domain ? 5 : 1;
  const score = Math.min(fit, 25) + intent + Math.min(clarity, 20) + budget + buyer + confidence;

  scored.push({
    key: (j.company_domain || String(j.company_candidate || '').toLowerCase()).trim(),
    name: j.company_candidate || '',
    domain: j.company_domain || '',
    signal_type: j.signal_type,
    score: score,
    bottlenecks: bottlenecks,
    stages: stages,
    modality: modOk.join('; '),
    failed: failed,
    question: question,
    url: j.source_url,
    date: j.signal_date || '',
    title: j.title || ''
  });
}

const groups = {};
for (const s of scored) {
  if (!s.key) continue;
  if (!groups[s.key]) groups[s.key] = [];
  groups[s.key].push(s);
}

const rows = [];

for (const key of Object.keys(groups)) {
  const group = groups[key].sort((a, b) => b.score - a.score);
  const best = group[0];

  const types = [];
  const bns = [];
  for (const g of group) {
    if (types.indexOf(g.signal_type) === -1) types.push(g.signal_type);
    for (const b of g.bottlenecks) { if (bns.indexOf(b) === -1) bns.push(b); }
  }

  const bonus = Math.min(8, 4 * (types.length - 1));
  const total = Math.min(100, best.score + bonus);

  const blocking = best.failed.filter(f => f.indexOf('G1') === 0 || f.indexOf('G5') === 0);

  let priority = 'Reject';
  if (total >= 80) priority = 'A';
  else if (total >= 68) priority = 'B';
  else if (total >= 55) priority = 'Review';

  if (blocking.length > 0 && (priority === 'A' || priority === 'B')) priority = 'Review';

  let status = (priority === 'A' || priority === 'B') ? 'Approve' : priority;
  let question = best.question;

  if (status === 'Approve' && !best.domain) {
    status = 'Review';
    priority = 'Review';
    question = question || 'resolve the company website and confirm asset ownership';
  }

  rows.push({
    json: {
      company_key: key,
      canonical_company: best.name,
      domain: best.domain,
      status: status,
      priority: priority,
      score: total,
      signal_count: group.length,
      signal_types: types.join('; '),
      corroboration_bonus: bonus,
      modality: best.modality,
      asset_stage: best.stages.join('; '),
      bottlenecks: bns.join('; '),
      top_signal_url: best.url,
      top_signal_date: best.date,
      top_signal_title: best.title,
      evidence_urls: group.slice(0, 6).map(g => g.url).join(' | '),
      failed_gates: best.failed.join('; '),
      open_question: question,
      reviewer: '',
      review_date: '',
      run_date: new Date().toISOString().slice(0, 10)
    }
  });
}

rows.sort((a, b) => b.json.score - a.json.score);
return rows;
`
    }
  },
  output: [{ company_key: 'novabinder.com', canonical_company: 'NovaBinder', domain: 'novabinder.com', status: 'Approve', priority: 'A', score: 93, signal_count: 2, signal_types: 'capital; hiring', corroboration_bonus: 4, modality: 'bispecific', asset_stage: 'lead_optimization', bottlenecks: 'binding_performance; sequence_risk', top_signal_url: 'https://novabinder.com/news/series-a', top_signal_date: '2026-07-09', top_signal_title: 'NovaBinder raises $42M Series A', evidence_urls: 'https://novabinder.com/news/series-a', failed_gates: '', open_question: '', reviewer: '', review_date: '', run_date: '2026-07-21' }]
});

const filterQualified = node({
  type: 'n8n-nodes-base.filter',
  version: 2.3,
  config: {
    name: 'Qualified For Human Review',
    position: [940, -20],
    parameters: {
      conditions: {
        options: { caseSensitive: true, leftValue: '', typeValidation: 'loose', version: 2 },
        conditions: [
          { id: 'not-reject', leftValue: expr('{{ $json.priority }}'), operator: { type: 'string', operation: 'notEquals' }, rightValue: 'Reject' }
        ],
        combinator: 'and'
      },
      looseTypeValidation: true
    }
  },
  output: [{ company_key: 'novabinder.com', canonical_company: 'NovaBinder', priority: 'A', score: 93 }]
});

const saveReviewQueue = node({
  type: 'n8n-nodes-base.googleSheets',
  version: 4.7,
  config: {
    name: 'Upsert Into Review Queue',
    position: [1160, -20],
    onError: 'continueRegularOutput',
    parameters: {
      resource: 'sheet',
      operation: 'appendOrUpdate',
      authentication: 'oAuth2',
      documentId: { __rl: true, mode: 'list', value: '', cachedResultName: 'Antibody Prospecting Review Queue' },
      sheetName: { __rl: true, mode: 'name', value: 'review_queue' },
      columns: {
        mappingMode: 'autoMapInputData',
        value: {},
        matchingColumns: ['company_key'],
        schema: [
          { id: 'company_key', displayName: 'company_key', required: false, defaultMatch: true, display: true, type: 'string', canBeUsedToMatch: true },
          { id: 'canonical_company', displayName: 'canonical_company', required: false, defaultMatch: false, display: true, type: 'string', canBeUsedToMatch: false },
          { id: 'domain', displayName: 'domain', required: false, defaultMatch: false, display: true, type: 'string', canBeUsedToMatch: false },
          { id: 'status', displayName: 'status', required: false, defaultMatch: false, display: true, type: 'string', canBeUsedToMatch: false },
          { id: 'priority', displayName: 'priority', required: false, defaultMatch: false, display: true, type: 'string', canBeUsedToMatch: false },
          { id: 'score', displayName: 'score', required: false, defaultMatch: false, display: true, type: 'number', canBeUsedToMatch: false },
          { id: 'signal_count', displayName: 'signal_count', required: false, defaultMatch: false, display: true, type: 'number', canBeUsedToMatch: false },
          { id: 'signal_types', displayName: 'signal_types', required: false, defaultMatch: false, display: true, type: 'string', canBeUsedToMatch: false },
          { id: 'modality', displayName: 'modality', required: false, defaultMatch: false, display: true, type: 'string', canBeUsedToMatch: false },
          { id: 'asset_stage', displayName: 'asset_stage', required: false, defaultMatch: false, display: true, type: 'string', canBeUsedToMatch: false },
          { id: 'bottlenecks', displayName: 'bottlenecks', required: false, defaultMatch: false, display: true, type: 'string', canBeUsedToMatch: false },
          { id: 'top_signal_url', displayName: 'top_signal_url', required: false, defaultMatch: false, display: true, type: 'string', canBeUsedToMatch: false },
          { id: 'top_signal_date', displayName: 'top_signal_date', required: false, defaultMatch: false, display: true, type: 'string', canBeUsedToMatch: false },
          { id: 'top_signal_title', displayName: 'top_signal_title', required: false, defaultMatch: false, display: true, type: 'string', canBeUsedToMatch: false },
          { id: 'evidence_urls', displayName: 'evidence_urls', required: false, defaultMatch: false, display: true, type: 'string', canBeUsedToMatch: false },
          { id: 'failed_gates', displayName: 'failed_gates', required: false, defaultMatch: false, display: true, type: 'string', canBeUsedToMatch: false },
          { id: 'open_question', displayName: 'open_question', required: false, defaultMatch: false, display: true, type: 'string', canBeUsedToMatch: false },
          { id: 'reviewer', displayName: 'reviewer', required: false, defaultMatch: false, display: true, type: 'string', canBeUsedToMatch: false },
          { id: 'review_date', displayName: 'review_date', required: false, defaultMatch: false, display: true, type: 'string', canBeUsedToMatch: false },
          { id: 'run_date', displayName: 'run_date', required: false, defaultMatch: false, display: true, type: 'string', canBeUsedToMatch: false }
        ]
      },
      options: { cellFormat: 'USER_ENTERED', handlingExtraData: 'insertInNewColumn' }
    },
    credentials: { googleSheetsOAuth2Api: newCredential('Google Sheets') }
  },
  output: [{ company_key: 'novabinder.com', canonical_company: 'NovaBinder', priority: 'A', score: 93 }]
});

const noteDiscovery = sticky(
  '## 1. Intent Discovery\n\n21 seed queries across five trigger families: capital, program/milestone, hiring, scientific, execution. Each seed carries its own recency window.\n\nTune the seed bank in the Code node. Every signal keeps its seed_id so you can retire queries that never produce approvals.',
  [buildSeeds, loopSeeds, tavilySearch, collectResults],
  { color: 4 }
);

const noteGate = sticky(
  '## 2. Exclusions and Scoring\n\nHard exclusions run BEFORE any extraction spend: CRO/CDMO, diagnostics, reagents, non-buyers, competitors.\n\nA domain resolves as the company only if its own name appears in the page title, otherwise trade press gets logged as a prospect.',
  [gatePassOne, filterSurvivors],
  { color: 3 }
);

const noteExtract = sticky(
  '## 3. Full-Text Pass\n\nSearch snippets are too short to prove a bottleneck. Survivors get their page fetched and rescored, which roughly doubles the qualified set.\n\nThis runs only on records that passed the exclusions, so no credits are spent on a known CRO.',
  [loopSignals, tavilyExtract, mergeFullText],
  { color: 5 }
);

const noteOutput = sticky(
  '## 4. Company Master and Handoff\n\nSignals collapse into one row per company. Independent trigger families add a corroboration bonus.\n\nThe workflow stops at the review queue. No contact or email enrichment happens until a human sets status to Approved.\n\nPick your spreadsheet in the Google Sheets node and add a tab named review_queue.',
  [buildCompanyMaster, filterQualified, saveReviewQueue],
  { color: 6 }
);

export default workflow('antibody-intent-prospecting', 'Antibody Intent Prospecting - Discovery to Review Queue')
  .add(dailyTrigger)
  .to(buildSeeds)
  .to(loopSeeds
    .onEachBatch(tavilySearch.to(collectResults.to(nextBatch(loopSeeds))))
    .onDone(gatePassOne
      .to(filterSurvivors)
      .to(loopSignals
        .onEachBatch(tavilyExtract.to(mergeFullText.to(nextBatch(loopSignals))))
        .onDone(buildCompanyMaster.to(filterQualified).to(saveReviewQueue))
      )
    )
  )
  .add(noteDiscovery)
  .add(noteGate)
  .add(noteExtract)
  .add(noteOutput);
