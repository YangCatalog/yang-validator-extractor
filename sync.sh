#!/usr/bin/env bash
#
# This script fetches all published IETF RFCs and drafts, and
# extracts them to a temporary directory.
#

YANG_TMPDIR=/var/tmp/yangmodules/work
YANG_EXTRACTDIR=/var/tmp/yangmodules/extracted

echo "Creating tmpdir $YANG_TMPDIR"
mkdir -pv $YANG_TMPDIR

echo "Creating extractdir $YANG_EXTRACTDIR"
mkdir -pv $YANG_EXTRACTDIR

echo "Fetching files into $YANG_TMPDIR"
rsync -az --no-l --include="draft*.txt" --exclude="*" --delete rsync.ietf.org::internet-drafts $YANG_TMPDIR/my-id-mirror
rsync -az --no-l --include="rfc*.txt"   --exclude="*" --delete rsync.ietf.org::rfc $YANG_TMPDIR/my-rfc-mirror

echo "Extracting modules into $YANG_EXTRACTDIR"
for file in $(find $YANG_TMPDIR/my-id-mirror/ -type f -exec \
  	          egrep -l '^[ \t]*(sub)?module +[\\'\"]?[-A-Za-z0-9]*[\\'\"]? *\{.*$' {} +);
	do xym --dstdir $YANG_EXTRACTDIR --strict True $file
done

for file in $(find $YANG_TMPDIR/my-rfc-mirror/ -type f -exec \
	          egrep -l '^[ \t]*(sub)?module +[\\'\"]?[-A-Za-z0-9]*[\\'\"]? *\{.*$' {} +);
	do xym --dstdir $YANG_EXTRACTDIR --strict True $file
done
