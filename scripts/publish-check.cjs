#!/usr/bin/env node
'use strict';
const fs=require('node:fs');const path=require('node:path');
const pkg=require('../package.json');
if(pkg.private===true) throw Error('package must be public');
if(!pkg.name||!pkg.bin?.['ai-dev']||!fs.existsSync(path.join(__dirname,'..',pkg.bin['ai-dev'])))throw Error('bin missing');
for(const p of ['scripts/external-install.py','scripts/workflow.py','templates/AGENTS.md','lib/install.js','lib/status.js'])if(!fs.existsSync(path.join(__dirname,'..',p)))throw Error('missing '+p);
console.log('PUBLISH_CHECK_PASS',pkg.name,pkg.version);
