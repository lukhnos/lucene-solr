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

# This script translates Java to Objective-C using the j2objc transpiler.
#
# It assumes that you're running in Lucene's source root, not Lucene-Solr's
# top-level directory.
#
# The script is a work in progress. It does not translate non-Lucene source
# code as it has a lot of hard-coded dependency information. Nor does it
# translate Lucene tests since they are not yet supported.

import fnmatch
import os
import subprocess
import sys
import re

from translate_common import LUCENE_SRC_PATHS

# These two classes should really be put into their own respective .java
# files, but they currently live in DocFreqValueSource.java.
#
# Another class, FragmentQueue, also has the same problem. It lives in
# Highlighter.java (of package org.apache.lucene.search.highlight), but since
# it's only used by Highlighter, it's less of a problem.
FAULTY_INCLUDES = (
    '#include "org/apache/lucene/queries/function/valuesource/ConstDoubleDocValues.h"',  # nopep8
    '#include "org/apache/lucene/queries/function/valuesource/ConstIntDocValues.h"',  # nopep8
)


FAULTY_INCLUDE_FIX = '#include "org/apache/lucene/queries/function/valuesource/DocFreqValueSource.h"  // fixed by translate.py'  # nopep8


DISABLE_INCLUDE = (
    '#include "org/apache/lucene/analysis/hunspell/ISO8859_14Decoder.h"',
    '+ (jint)PAGE_SIZE;'
)


FAULTY_HEADER_FILE = './build/objc/org/apache/lucene/index/DocValuesFieldUpdates.h'  # nopep8


FAULTY_INCLUDE_REGEX = r'^\+ \(jint\)PAGE_SIZE[ ]*{[A-Za-z_ \n;]+}$'


DISABLE_SUFFIX = ' // disabled by translate.py'


def postprocess_translated_objc(path):
    """
    Postprocess translated Objective-C code.
    """

    if not os.path.exists(path):
        print('Error: file does not exist at path: %s' % path)
        return 0

    with open(path) as f:
        code = f.read()

    new_code = code

    for substr in FAULTY_INCLUDES:
        new_code = new_code.replace(substr, FAULTY_INCLUDE_FIX)

    for substr in DISABLE_INCLUDE:
        new_code = new_code.replace(substr, '// ' + substr + DISABLE_SUFFIX)

    page_size_line = re.search(FAULTY_INCLUDE_REGEX, new_code, re.M | re.I)
    if page_size_line:
        new_code = new_code.replace(page_size_line.group(), '/* ' + page_size_line.group() + ' */' + DISABLE_SUFFIX)  # nopep8

    new_code = new_code.replace(
        'return create_OrgApacheLuceneAnalysisHunspellISO8859_14Decoder_initPackagePrivate();',  # nopep8
        '@throw [new_JavaLangRuntimeException_initWithNSString_(@"Not translated to Objective-C") autorelease];' + DISABLE_SUFFIX  # nopep8
    )

    if new_code != code:
        with open(path, 'w') as f:
            print('Post processing Objective-C code: %s' % path)
            f.write(new_code)
            return 1
    return 0

extra_cps = (
    # Should not be needed if we skip sandbox/queries/regex
    './sandbox/lib/jakarta-regexp-1.4.jar',

    # fix ConstDoubleDocValues
    './build/queries/classes/java'
)

excluded = (
    # No need to translate j2objc annotations to Objective-C.
    './core/src/java/org/lukhnos/portmobile/j2objc/*',

    # Currently skipped; these currently relies on JDK 7's BreakIterator,
    # which, although supported on Android, is not implemented by j2objc's
    # jre_emul. See the discussion here for porting considerations:
    # https://groups.google.com/forum/#!topic/j2objc-discuss/Rx7ioYfOaIU
    './analysis/common/src/java/org/apache/lucene/analysis/hunspell/ISO8859_14Decoder.java',  # nopep8
    './analysis/common/src/java/org/apache/lucene/analysis/th/*.java',
    './analysis/common/src/java/org/apache/lucene/analysis/util/CharArrayIterator.java',  # nopep8
    './analysis/common/src/java/org/apache/lucene/analysis/util/SegmentingTokenizerBase.java',  # nopep8

    # Requires antlr.
    './expressions/src/java/org/apache/lucene/expressions/js/*.java',

    # Requires BreakIterator.
    './highlighter/src/java/org/apache/lucene/search/postingshighlight/*.java',  # nopep8
    './highlighter/src/java/org/apache/lucene/search/vectorhighlight/*.java',  # nopep8

    # Not used.
    './grouping/src/java/org/apache/lucene/search/grouping/*.java',
    './grouping/src/java/org/apache/lucene/search/grouping/function/*.java',
    './grouping/src/java/org/apache/lucene/search/grouping/term/*.java',

    # Depends on Grouping
    './join/src/java/org/apache/lucene/search/join/ToParentBlockJoinCollector.java',  # nopep8

    # Uses native methods.
    './misc/src/java/org/apache/lucene/store/*.java',

    # Not used.
    './misc/src/java/org/apache/lucene/uninverting/*.java',

    # Gone from 5.3.x (used to be in Lucene 5.2.1)
    # './misc/src/java/org/apache/lucene/misc/store/*.java',
    # './misc/src/java/org/apache/lucene/misc/uninverting/*.java',

    # Currently skipped; it relies on ./sandbox/lib/jakarta-regexp-1.4.jar
    # and we don't have that library translated to Objective-C yet.
    './sandbox/src/java/org/apache/lucene/sandbox/queries/regex/*.java'
    # './sandbox/src/java/org/apache/lucene/queries/regex/*.java',
)

dst = './build/objc'
j2objc = './j2objc/j2objc'

if not os.path.exists(j2objc):
    print('j2objc not found. Please execute the following script to fetch and setup the latest version of j2objc:')  # nopep8
    print('$> ./setup-j2objc.sh')
    sys.exit(1)

if not os.path.exists(dst):
    os.makedirs(dst)
    print('Destination directory created: %s\n' % dst)

classpaths = LUCENE_SRC_PATHS + extra_cps
print('using path:\n%s\n' % '\n'.join(classpaths))

total_compiled_files = 0
total_post_processed_files = 0

for src in classpaths:
    to_compile = []
    to_postprocess = []

    for base, dirs, files in os.walk(src):
        for file_path in files:
            if not fnmatch.fnmatch(file_path, "*.java"):
                continue

            full_path_java = os.path.join(base, file_path)
            if any(fnmatch.fnmatch(full_path_java, ptn) for ptn in excluded):
                continue

            full_path_m = full_path_java.replace(src, dst).replace(".java", ".m")  # nopep8
            if os.path.exists(full_path_m):
                if os.path.getmtime(full_path_m) >= os.path.getmtime(full_path_java):  # nopep8
                    continue

            to_compile.append(full_path_java)
            to_postprocess.append(full_path_m)

    print('\nTranslating: %s with %d java files to compile.\n' % (src, len(to_compile)))  # nopep8

    if to_compile:
        args = [
            j2objc,
            '-d', dst,
            '-classpath', ':'.join(classpaths),
            '--swift-friendly',
            '--nullability',
            '--doc-comments'
        ]
        args.extend(to_compile)
        ec = subprocess.call(args)
        if ec != 0:
            print('\nExit with error code: %d\n' % ec)
            sys.exit(1)
        # TODO: Check error code

    total_compiled_files += len(to_compile)

    post_processed_files = 0
    for path in to_postprocess:
        post_processed_files += postprocess_translated_objc(path)

    print('Did post process %d obj-c files.\n' % post_processed_files)
    total_post_processed_files += post_processed_files

# Post process specific header files.
post_processed_files += postprocess_translated_objc(FAULTY_HEADER_FILE)

print("\nDone. %d files compiled into Objective-C including %d post processed files.\n" % (total_compiled_files, total_post_processed_files))  # nopep8
