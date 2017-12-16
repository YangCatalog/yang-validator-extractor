TMPDIR=$(mktemp -d /tmp/ietfmirror.XXXXXX)
echo "Fetching files into $TMPDIR"

rsync -avz --no-l --include="draft*.txt" --exclude="*" --delete rsync.ietf.org::internet-drafts $TMPDIR/my-id-mirror
rsync -avz --no-l --include="rfc*.txt"   --exclude="*" --delete rsync.ietf.org::rfc $TMPDIR/my-rfc-mirror

mkdir $TMPDIR/all-yang

for file in $(egrep -l '^[ \t]*(sub)?module +[\\'\"]?[-A-Za-z0-9]*[\\'\"]? *\{.*$' $TMPDIR/my-id-mirror/*)  ; do xym --dstdir $TMPDIR/all-yang --strict True $file; done
for file in $(egrep -l '^[ \t]*(sub)?module +[\\'\"]?[-A-Za-z0-9]*[\\'\"]? *\{.*$' $TMPDIR/my-rfc-mirror/*) ; do xym --dstdir $TMPDIR/all-yang --strict True $file; done

tar --exclude="example*" -zcvf ./all-yang.tgz -C $TMPDIR all-yang

rm -rf $TMPDIR