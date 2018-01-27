#
# This script fetches all published IETF RFCs and drafts, extracts any
# found YANG modules and packs it up in a tarball.
#

TMPDIR=$(mktemp -d /var/tmp/yangmodules)
if [ $? -ne 0 ]; then
	echo "$0: Can't create temp file, exiting..."
	exit 1
fi

echo "Fetching files into $TMPDIR"

rsync -az --no-l --include="draft*.txt" --exclude="*" --delete rsync.ietf.org::internet-drafts $TMPDIR/my-id-mirror
rsync -az --no-l --include="rfc*.txt"   --exclude="*" --delete rsync.ietf.org::rfc $TMPDIR/my-rfc-mirror

mkdir $TMPDIR/all-yang

for file in $(egrep -l '^[ \t]*(sub)?module +[\\'\"]?[-A-Za-z0-9]*[\\'\"]? *\{.*$' $TMPDIR/my-id-mirror/*)  ; do xym --dstdir $TMPDIR/all-yang --strict True $file; done
for file in $(egrep -l '^[ \t]*(sub)?module +[\\'\"]?[-A-Za-z0-9]*[\\'\"]? *\{.*$' $TMPDIR/my-rfc-mirror/*) ; do xym --dstdir $TMPDIR/all-yang --strict True $file; done

# Should probably exclude more weird non-useful modules here
tar --exclude="example*" -zcvf ./all-yang.tgz -C $TMPDIR all-yang

rm -rf mkdir $TMPDIR/all-yang