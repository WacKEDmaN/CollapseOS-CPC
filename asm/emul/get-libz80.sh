#!/bin/sh -e
# Fetch libz80 at the commit this Collapse OS snapshot was made with.
# (Upstream used a git submodule; this copy lives inside another repo.)
cd "$(dirname "$0")"
[ -d libz80/.git ] || git clone https://github.com/ggambetta/libz80.git libz80
git -C libz80 checkout -q 8a1f935daa3c288b68121051e8e45068684f80a4
echo "libz80 ready at 8a1f935"
