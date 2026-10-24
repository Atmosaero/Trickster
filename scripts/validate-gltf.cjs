const fs = require('fs');
const path = require('path');
const validator = require('../artifacts/validator/node_modules/gltf-validator');
(async () => {
  let errors = 0;
  for (const filename of process.argv.slice(2)) {
    const bytes = new Uint8Array(fs.readFileSync(filename));
    const report = await validator.validateBytes(bytes, {uri: path.basename(filename), maxIssues: 100, externalResourceFunction: uri => Promise.resolve(new Uint8Array(fs.readFileSync(path.resolve(path.dirname(filename), uri))))});
    fs.writeFileSync(filename + '.report.json', JSON.stringify(report, null, 2));
    console.log(`${filename}: ${report.issues.numErrors} errors, ${report.issues.numWarnings} warnings`);
    for (const issue of report.issues.messages.slice(0, 8)) console.log(`  ${issue.code}: ${issue.message}`);
    errors += report.issues.numErrors;
  }
  process.exitCode = errors ? 1 : 0;
})().catch(error => { console.error(error); process.exitCode = 1; });
