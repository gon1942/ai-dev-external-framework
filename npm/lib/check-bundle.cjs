'use strict';
const fs = require('node:fs');
const path = require('node:path');
const pkg = require('../package.json');
const wheel = path.join(__dirname, '../vendor', `team_ai_dev_framework-${pkg.version}-py3-none-any.whl`);
if (!fs.existsSync(wheel)) { console.error('npm 배포 차단: Python WHL이 vendor/에 없습니다:', wheel); process.exit(1); }
console.log('Python engine bundle OK:', path.basename(wheel));
