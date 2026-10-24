"""Collect notices for the Qt SDK used by this build; no libraries are modified."""
import concurrent.futures, json, pathlib, re, shutil, sys, urllib.request
sdk = pathlib.Path(sys.argv[1])
out = pathlib.Path('licenses'); out.mkdir(exist_ok=True)
spdx = sdk / 'sbom' / 'qtbase-6.12.0.spdx.json'
info = json.loads(spdx.read_text(encoding='utf-8'))
shutil.copyfile(spdx, out / spdx.name)
ids = set(['LGPL-3.0-only', 'GPL-3.0-only'])
for package in info['packages']:
    ids.update(re.findall(r'[A-Za-z0-9][A-Za-z0-9.+-]*', package.get('licenseConcluded', '')))
ids.difference_update(['AND','OR','WITH','NOASSERTION','NONE','Linux-syscall-note','Qt-GPL-exception-1.0'])
ids = [i for i in ids if not i.startswith('LicenseRef-')]
for entry in info.get('hasExtractedLicensingInfos',[]):
    if entry['licenseId'] != 'LicenseRef-Qt-Commercial':
        (out/(entry['licenseId']+'.txt')).write_text(entry.get('extractedText',''),encoding='utf-8')
def download(identifier):
    url = 'https://raw.githubusercontent.com/spdx/license-list-data/main/text/' + identifier + '.txt'
    with urllib.request.urlopen(url,timeout=30) as response:
        (out/(identifier+'.txt')).write_bytes(response.read())
    return identifier
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
    for identifier in pool.map(download, sorted(ids)):
        print(identifier)
