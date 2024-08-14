#!/bin/bash

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
	cd build/python3.10_release && cp -v * /boot/system/non-packaged/lib/python3.10/site-packages/Be
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
	ln -s /boot/home/config/non-packaged/bin/HTMZ.py /boot/home/config/settings/deskbar/menu/Applications/HTMZ
	ret5=$?
else
	echo Main program missing
	ret4=1
	ret5=1
fi
echo
alt="$(uname -p)"
txt="x86_64"
if [ "$alt" = "$txt" ]; then
if [ -e DecompressTMZ.tmz ]
then
	2>/dev/null 1>&2 ./HTMZ.py -d DecompressTMZ.tmz -g
	if [ -e DecompressTMZ ]; then
		mv DecompressTMZ/DecompressTMZ /boot/home/config/non-packaged/bin/
		ret6=$?
		rm -rf DecompressTMZ
	fi
else
	ret6=1
fi
else
if [ -e DecompressTMZx86.tmz ]
then
	2>/dev/null 1>&2 ./HTMZ.py -d DecompressTMZx86.tmz -g
	if [ -e DecompressTMZx86 ]; then
		mv DecompressTMZx86/DecompressTMZ /boot/home/config/non-packaged/bin/
		ret6=$?
		rm -rf DecompressTMZx86
	fi
else
	ret6=1
fi
fi

if [ -e x-tmz.tmz ]
then
	2>/dev/null 1>&2 ./HTMZ.py -d x-tmz.tmz -g
	if [ -e x-tmz ]; then
		mv x-tmz/x-tmz /boot/home/config/settings/mime_db/application/
		ret8=$?
		rm -rf x-tmz
	else
		ret8=1
	fi
else
	ret8=1
fi

if [ $ret2 -lt 1 ]
then
	echo -e "Installation of Haiku-PyAPI \e[37;42mOK\e[0m"
	if [ $ret7 -lt 1 ]
	then
		echo -e "Copy of Haiku-PyAPI libraries in python site-packages \e[37;42mOK\e[0m"
	else
		echo -e "Copy of Haiku-PyAPI libraries in python site-packages \e[37;41mFAILED\e[0m"
	fi
else
	echo -e "Installation of Haiku-PyAPI \e[37;41mFAILED\e[0m"
fi

if [ $ret4 -lt 1 ] 
then
        echo -e "Installation of HTPBZ2 \e[37;42mOK\e[0m"
else
        echo -e Installation of HTPBZ2 "\e[37;41mFAILED\e[0m"
fi
if [ $ret5 -lt 1 ] 
then
        echo -e "Deskbar menu entry installation \e[37;42mOK\e[0m"
else
        echo -e Deskbar menu entry installation "\e[37;41mFAILED\e[0m"
fi

if [ $ret6 -lt 1 ] 
then
        echo -e "Decompressor launcher installation \e[37;42mOK\e[0m"
else
        echo -e Decompressor launcher installation "\e[37;41mFAILED\e[0m"
fi
if [ $ret8 -lt 1 ] 
then
        echo -e "FileType installation \e[37;42mOK\e[0m"
else
        echo -e FileType installation "\e[37;41mFAILED\e[0m"
fi
