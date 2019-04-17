GIT_SSH_KEY=~/.ssh/id_rsa_grass-svn2git

VER=3_2_0
COMMIT=a3c282d
git checkout $COMMIT
GIT_COMMITTER_DATE="$(git show --format=%aD | head -1)" git tag -a grass_$VER -m"grass_$VER"
git checkout master
GIT_SSH_COMMAND="ssh -i ${GIT_SSH_KEY}" git push --tags

VER=4_0_0
COMMIT=8098eb4
git checkout $COMMIT
GIT_COMMITTER_DATE="$(git show --format=%aD | head -1)" git tag -a grass_$VER -m"grass_$VER"
git checkout master
GIT_SSH_COMMAND="ssh -i ${GIT_SSH_KEY}" git push --tags

VER=4_1_0
COMMIT=597f833
git checkout $COMMIT
GIT_COMMITTER_DATE="$(git show --format=%aD | head -1)" git tag -a grass_$VER -m"grass_$VER"
git checkout master
GIT_SSH_COMMAND="ssh -i ${GIT_SSH_KEY}" git push --tags

VER=4_2_0
COMMIT=b8d4ada
git checkout $COMMIT
GIT_COMMITTER_DATE="$(git show --format=%aD | head -1)" git tag -a grass_$VER -m"grass_$VER"
git checkout master
GIT_SSH_COMMAND="ssh -i ${GIT_SSH_KEY}" git push --tags

VER=4_3_0
COMMIT=b18eb5b
git checkout $COMMIT
GIT_COMMITTER_DATE="$(git show --format=%aD | head -1)" git tag -a grass_$VER -m"grass_$VER"
git checkout master
GIT_SSH_COMMAND="ssh -i ${GIT_SSH_KEY}" git push --tags

VER=5_0_0
COMMIT=69b7d34
git checkout $COMMIT
GIT_COMMITTER_DATE="$(git show --format=%aD | head -1)" git tag -a grass_$VER -m"grass_$VER"
git checkout master
GIT_SSH_COMMAND="ssh -i ${GIT_SSH_KEY}" git push --tags

VER=5_4_0
COMMIT=80fee7a
git checkout $COMMIT
GIT_COMMITTER_DATE="$(git show --format=%aD | head -1)" git tag -a grass_$VER -m"grass_$VER"
git checkout master
GIT_SSH_COMMAND="ssh -i ${GIT_SSH_KEY}" git push --tags

VER=5_5_0
COMMIT=58aed09
git checkout $COMMIT
GIT_COMMITTER_DATE="$(git show --format=%aD | head -1)" git tag -a grass_$VER -m"grass_$VER"
git checkout master
GIT_SSH_COMMAND="ssh -i ${GIT_SSH_KEY}" git push --tags

VER=6_0_0
COMMIT=3046610
git checkout $COMMIT
GIT_COMMITTER_DATE="$(git show --format=%aD | head -1)" git tag -a grass_$VER -m"grass_$VER"
git checkout master
GIT_SSH_COMMAND="ssh -i ${GIT_SSH_KEY}" git push --tags

VER=6_1_0
COMMIT=86c4977
git checkout $COMMIT
GIT_COMMITTER_DATE="$(git show --format=%aD | head -1)" git tag -a grass_$VER -m"grass_$VER"
git checkout master
GIT_SSH_COMMAND="ssh -i ${GIT_SSH_KEY}" git push --tags

VER=6_2_0
COMMIT=8bcb2cb
git checkout $COMMIT
GIT_COMMITTER_DATE="$(git show --format=%aD | head -1)" git tag -a grass_$VER -m"grass_$VER"
git checkout master
GIT_SSH_COMMAND="ssh -i ${GIT_SSH_KEY}" git push --tags

VER=6_3_0
COMMIT=ec982a2
git checkout $COMMIT
GIT_COMMITTER_DATE="$(git show --format=%aD | head -1)" git tag -a grass_$VER -m"grass_$VER"
git checkout master
GIT_SSH_COMMAND="ssh -i ${GIT_SSH_KEY}" git push --tags

VER=6_4_0
COMMIT=fb6af76
git checkout $COMMIT
GIT_COMMITTER_DATE="$(git show --format=%aD | head -1)" git tag -a grass_$VER -m"grass_$VER"
git checkout master
GIT_SSH_COMMAND="ssh -i ${GIT_SSH_KEY}" git push --tags

git checkout master
