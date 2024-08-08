#!/bin/bash
#ret3
echo "Do you wish to git clone & compile Haiku-PyAPI to your system? (type y or n)"
read text
if [ $text == "y" ]
then
git clone --recurse-submodules https://github.com/coolcoder613eb/Haiku-PyAPI.git
cd Haiku-PyAPI
jam -j$(nproc)
ret2=$?
if [ $ret2 -lt 1 ]
then
	if ! [[ -e /boot/system/non-packaged/lib/python3.10/site-packages/Be ]]; then
		mkdir /boot/system/non-packaged/lib/python3.10/site-packages/Be
	fi
	echo "copying compiled data to system folder..."
	cd bin/x86_64/python3.10 && cp -v * /boot/system/non-packaged/lib/python3.10/site-packages/Be
	ret7=$?
	cd ../../..
fi
cd ..
else
echo "Proceeding..."
ret2=1
fi
echo
if [ -e HTMZ.py ]
then
	if ! [[ -e /boot/home/config/non-packaged/data/HTPBZ2 ]]; then
		mkdir /boot/home/config/non-packaged/data/HTPBZ2
	fi
	cp HTMZ.py /boot/home/config/non-packaged/data/HTPBZ2
	ret4=$?
	if [ -e /boot/home/config/non-packaged/bin/HTMZ.py ]; then
		rm -f /boot/home/config/non-packaged/bin/HTMZ.py
	fi
	ln -s /boot/home/config/non-packaged/data/HTPBZ2/HTMZ.py /boot/home/config/non-packaged/bin/HTMZ.py
	if ! [[ -e /boot/home/config/settings/deskbar/menu/Applications/ ]]; then
		mkdir /boot/home/config/settings/deskbar/menu/Applications/
	fi
	#ret5
else
	echo Main program missing
	ret4=1
	#ret5=1
fi
echo
#ret6
if [ -e DecompressTMZ.tmz ]
then
	./HTMZ.py -d DecompressTMZ.tmz -g
	if [ -e DecompressTMZ ]; then
		mv DecompressTMZ/DecompressTMZ /boot/home/config/non-packaged/bin/
		ret6=$?
	fi
else
	ret6=1
fi

if [ $ret2 -lt 1 ]
then
	echo Installation of Haiku-PyAPI OK
	if [ $ret7 -lt 1 ]
	then
		echo Copy of Haiku-PyAPI libraries in python site-packages OK
	else
		echo Copy of Haiku-PyAPI libraries in python site-packages FAILED
	fi
else
	echo Installation of Haiku-PyAPI FAILED
fi

if [ $ret4 -lt 1 ] 
then
        echo Installation of HTPBZ2 OK
else
        echo Installation of HTPBZ2 FAILED
fi
if [ $ret6 -lt 1 ] 
then
        echo Decompressor launcher installation OK
else
        echo Decompressor launcher installation FAILED
fi

