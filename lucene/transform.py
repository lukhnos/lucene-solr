#!/usr/bin/env python
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# This script transforms the Lucene source code with some systematic rules
# so that the code can be used on Android and translated into Objective-C.
#
# Currently this does not handle Lucene tests since they are not yet
# supported.

import fnmatch
import os
import re
import sys

from translate_common import LUCENE_SRC_PATHS

import_map = {
    'java.nio.file.': 'org.lukhnos.portmobile.file.',
    'java.nio.file.attribute.': 'org.lukhnos.portmobile.file.attribute.',
    'java.lang.invoke.': 'org.lukhnos.portmobile.invoke.',
    'java.util.Objects': 'org.lukhnos.portmobile.util.Objects',
    'java.nio.charset.StandardCharsets': 'org.lukhnos.portmobile.charset.StandardCharsets',  # nopep8
}

import_map_re = {
    re.compile(re.escape(k)): v for k, v in import_map.items()
}

extra_imports = {
    'FileChannel.open': 'org.lukhnos.portmobile.channels.utils.FileChannelUtils',  # nopep8
    'new ClassValue': 'org.lukhnos.portmobile.lang.ClassValue',
    '// j2objc:"Weak"': 'org.lukhnos.portmobile.j2objc.annotations.Weak',
    '// j2objc:"WeakOuter"': 'org.lukhnos.portmobile.j2objc.annotations.WeakOuter',  # nopep8
}

extra_imports_re = {
    re.compile(re.escape(k), re.M | re.S): v for k, v in extra_imports.items()
}

method_calls = {
    'FileChannel.open': 'FileChannelUtils.open',
    '// j2objc:"Weak"': '@Weak',
    '// j2objc:"WeakOuter"': '@WeakOuter',
}

method_calls_re = {
    re.compile(re.escape(k), re.M | re.S): v for k, v in method_calls.items()
}

comments = {
    '{@link Files#newByteChannel(Path, java.nio.file.OpenOption...)}.':
        '{@link Files#newByteChannel(Path, org.lukhnos.portmobile.file.StandardOpenOption)}'  # nopep8
}

comments_re = {
    re.compile(re.escape(k), re.M | re.S): v for k, v in comments.items()
}

other_re = {
    re.compile(r'ReflectiveOperationException(\s*\|\s*\w*?Exception)?', re.M | re.S): 'Exception',  # nopep8
}

extra_import_tagline = '// Extra imports by portmobile.'


CODE_BLOCK_RE = re.compile(r'(.+import\s+.+?\n)(.+)', re.M | re.S)


def process_source(path):
    with open(path) as f:
        code = f.read()

    m = CODE_BLOCK_RE.match(code)
    if not m:
        return 0

    head_lines = m.group(1).split('\n')
    body = m.group(2)

    new_head_lines = []
    for line in head_lines:
        text = line
        for p, r in import_map_re.items():
            text = p.sub(r, text)
        new_head_lines.append(text)

    extras = []
    for p, i in extra_imports_re.items():
        if p.search(body):
            extras.append('import %s;' % i)

    if extras and not extra_import_tagline in head_lines:
        new_head_lines.append(extra_import_tagline)
        new_head_lines.extend(extras)
        new_head_lines.append('')

    new_body = body
    for p, r in method_calls_re.items():
        new_body = p.sub(r, new_body)

    for p, r in comments_re.items():
        new_body = p.sub(r, new_body)

    for p, r in other_re.items():
        new_body = p.sub(r, new_body)

    new_code = '\n'.join(new_head_lines) + new_body

    if head_lines != new_head_lines or body != new_body:
        with open(path, 'w') as f:
            print('Transform code:' + path)
            f.write(new_code)
            return 1
    return 0


def process_folder(src_path, count, modified):
    for base, dirs, files in os.walk(src_path):
        for file_path in files:
            if not fnmatch.fnmatch(file_path, "*.java"):
                continue
            full_path_java = os.path.join(base, file_path)
            if 'test' in full_path_java:
                # print('ignoring test file: ' + full_path_java)
                continue
            print('processing: ' + full_path_java)
            count += 1
            modified += process_source(full_path_java)
    return (count, modified)

count = 0
modified = 0
if len(sys.argv) > 1:
    print('using path:\n%s' % sys.argv[1])
    (count, modified) = process_folder(sys.argv[1], count, modified)
else:
    src_paths = LUCENE_SRC_PATHS
    print('using path:\n%s' % '\n'.join(src_paths))
    for src_path in src_paths:
        (count, modified) = process_folder(src_path, count, modified)

print("Done: %i files processed, %i files modified" % (count, modified))
