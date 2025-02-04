echo "INSTALLING PREREQUISITES..."
pkg install git


echo "Select repository from wich Turnip will be built: "
echo ""
echo "1) Pippeto-crypto's Mesa"
echo "2) Main Mesa"
echo ""
read -p "Option: " source
echo ""
if [ "$source" == "1" ]; then
    source="Pipetto-crypto"
else if [ "$source" == "2" ]; then
    source="mesa"
else
    echo "No source selected"
    sleep 2
    ./install.sh
    exit 0
fi
fi
read -p "Select branch (left empty for default): " branch
echo ""
if [ "$branch" == "" ]; then
    branch="main"
fi
status="$(curl -o /dev/null -s -w "%{http_code}\n" https://gitlab.freedesktop.org/$source/mesa/-/tree/$branch?ref_type=heads)"
while [ "$status" != "200" ]; do
    read -p "Branch doesn't exist. Try again: " branch
    status="$(curl -o /dev/null -s -w "%{http_code}\n" https://gitlab.freedesktop.org/$source/mesa/-/tree/$branch?ref_type=heads)"
done

git clone https://gitlab.freedesktop.org/$source/mesa.git -b $branch --recurse-submodules