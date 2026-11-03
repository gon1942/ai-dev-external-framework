#!/usr/bin/env node
'use strict';
try { require('../lib/bootstrap.cjs').main(); }
catch (e) { console.error(`[team-ai-dev] ${e.message}`); process.exitCode = 1; }
