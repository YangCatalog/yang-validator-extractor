#
# This script fetches all published IETF RFCs and drafts, extracts any
# found YANG modules and packs it up in a tarball.
#
TMPDIR=/var/tmp/yangmodules/work
EXTRACTDIR=/var/tmp/yangmodules/extracted
mkdir -pv $TMPDIR
mkdir -pv $EXTRACTDIR

if [ $? -ne 0 ]; then
	echo "$0: Can't create temp directory, exiting..."
	exit 1
fi

echo "Fetching files into $TMPDIR"

rsync -az --no-l --include="draft*.txt" --exclude="*" --delete rsync.ietf.org::internet-drafts $TMPDIR/my-id-mirror
rsync -az --no-l --include="rfc*.txt"   --exclude="*" --delete rsync.ietf.org::rfc $TMPDIR/my-rfc-mirror

for file in $(egrep -l '^[ \t]*(sub)?module +[\\'\"]?[-A-Za-z0-9]*[\\'\"]? *\{.*$' $TMPDIR/my-id-mirror/*)  ; do xym --dstdir $EXTRACTDIR --strict True $file; done
for file in $(egrep -l '^[ \t]*(sub)?module +[\\'\"]?[-A-Za-z0-9]*[\\'\"]? *\{.*$' $TMPDIR/my-rfc-mirror/*) ; do xym --dstdir $EXTRACTDIR --strict True $file; done

