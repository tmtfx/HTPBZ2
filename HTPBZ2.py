#!/boot/system/bin/python3
import os,sys
import tarfile
import bz2
import multiprocessing
from functools import partial
from Be import BApplication, BWindow, BView, BNode,BRadioButton,BButton,BMessage, window_type, B_NOT_RESIZABLE, B_CLOSE_ON_ESCAPE, B_QUIT_ON_WINDOW_CLOSE, BTextControl, BAlert,BListView, BScrollView,BListItem,BStringItem,BTextView,BRect, BBox, BFont, InterfaceDefs, BPath, BDirectory, BEntry,BStringView,BSlider
from Be import BFile,BCheckBox
from Be.FindDirectory import *
from Be.Alert import alert_type
from Be.InterfaceDefs import border_style,orientation
from Be.ListView import list_view_type
from Be.AppDefs import *
from Be.View import *
from Be.GraphicsDefs import *
from Be.Font import be_plain_font, be_bold_font
from Be import AppDefs
from Be.FilePanel import *
from Be.Application import *
from Be.Font import font_height,B_OUTLINED_FACE,B_ITALIC_FACE
from Be.Entry import entry_ref, get_ref_for_path
from Be.StorageDefs import node_flavor
from Be.TextView import text_run, text_run_array
from Be.Slider import hash_mark_location
import json
import io
import base64
import datetime
import struct
import math
import hashlib
import configparser
from pathlib import Path

Config=configparser.ConfigParser()
global ver,status,rev
ver="1"
status="alpha"
rev="20240722"
author="Fabio Tomat"

def ConfigSectionMap(section):
    dict1 = {}
    options = Config.options(section)
    for option in options:
        try:
            dict1[option] = Config.get(section, option)
            if dict1[option] == -1:
                DebugPrint("skip: %s" % option)
        except:
            print("exception on %s!" % option)
            dict1[option] = None
    return dict1

class ScrollView:
	HiWhat = 53 #Doppioclick
	SectionSelection = 54

	def __init__(self, rect, name):
		self.lv = BListView(rect, name, list_view_type.B_SINGLE_SELECTION_LIST)
		self.lv.SetResizingMode(B_FOLLOW_TOP_BOTTOM)
		self.lv.SetSelectionMessage(BMessage(self.SectionSelection))
		self.lv.SetInvocationMessage(BMessage(self.HiWhat))
		self.sv = BScrollView(name, self.lv,B_FOLLOW_NONE,0,False,False,border_style.B_FANCY_BORDER)
		self.sv.SetResizingMode(B_FOLLOW_TOP_BOTTOM)

class AboutView(BView):
	def __init__(self,frame):
		global rev,status,ver,author
		BView.__init__(self,frame,"About",8,20000000)
		bounds=self.Bounds()
		fon=BFont()
		fon.SetSize(24)
		font_height_value=font_height()
		fon.GetHeight(font_height_value)
		fon.SetShear(115.0)
		txt="Haiku Tar-ParallelBZip2"
		txtw=fon.StringWidth(txt)
		r=BRect(bounds.Width()/2-txtw/2-4,4,bounds.Width()/2+txtw/2+4,font_height_value.ascent+4)
		self.name=BStringView(r,"app_name",txt)
		self.name.SetFont(fon)
		self.name.SetHighColor(255,0,0,0)
		self.AddChild(self.name,None)
		txt="This simple utility compresses and decompresses files and folders in tar.bz2 format, and also adds Haiku-specific attributes to the archive.\nThe BZip2 compression is parallelized."
		abrect=BRect(4,font_height_value.ascent+8, bounds.Width()-4,bounds.Height()/2-4)
		inner_ab=BRect(4,4,abrect.Width()-4,abrect.Height()-4)
		self.AboutText = BTextView(abrect, 'aBOUTTxTView', inner_ab , B_FOLLOW_NONE)
		self.AboutText.MakeEditable(False)
		self.AboutText.MakeSelectable(False)
		fon1=BFont(be_plain_font)
		fon1.SetSize(14.0)
		col1=rgb_color()
		col1.red=10
		col1.green=200
		col1.blue=10
		col1.alpha=200
		self.AboutText.SetFontAndColor(fon1,B_FONT_ALL,col1)
		self.AboutText.SetText(txt,None)
		self.AddChild(self.AboutText,None)
#		perc=BPath()
#		find_directory(directory_which.B_USER_NONPACKAGED_DATA_DIRECTORY,perc,False,None)
#		ent=BEntry(perc.Path()+"/HTPBZ2")
#		if not ent.Exists():
#			self.Close()
#		else:
#			ent.GetPath(perc)
#			confile=BPath(perc.Path()+'/config.ini',None,False)
#			ent=BEntry(confile.Path())
#			if ent.Exists():
#				Config.read(confile.Path())
#				ver=ConfigSectionMap("About")["version"]
#				status=ConfigSectionMap("About")["status"]
#				rev=ConfigSectionMap("About")["revision"]
		txt="Version: "+ver
		r=BRect(4,bounds.Height()/2+4,self.StringWidth(txt)+4,font_height_value.ascent+bounds.Height()/2+4)
		self.version=BStringView(r,"app_ver",txt)
		self.AddChild(self.version,None)
		txt="Status: "+status
		r=BRect(4,font_height_value.ascent+bounds.Height()/2+8,self.StringWidth(txt)+4,font_height_value.ascent*2+bounds.Height()/2+12)
		self.status=BStringView(r,"app_status",txt)
		self.AddChild(self.status,None)
		txt="Rev: "+rev
		r=BRect(4,font_height_value.ascent*2+bounds.Height()/2+16,self.StringWidth(txt)+4,font_height_value.ascent*3+bounds.Height()/2+20)
		self.rev=BStringView(r,"app_rev",txt)
		self.AddChild(self.rev,None)
		txt="  By TmTFx"
		fon.GetHeight(font_height_value)
		fon.SetRotation(20.0)
		fon.SetShear(90.0)
		r = BRect(bounds.Width()/2,bounds.Height()/2+8,fon.StringWidth(txt)+bounds.Width()/2+16,bounds.Height()-4)
		self.author=BStringView(r,"app_auth",txt)
		self.author.SetFont(fon)
		self.AddChild(self.author,None)
				
class SystemView(BView):
	def __init__(self,frame):
		global endianness
		BView.__init__(self,frame,"About",8,20000000)
		bounds=self.Bounds()
		
		self.endianbox=BBox(BRect(4,4,bounds.Width()-4,bounds.Height()/2-4),"endianess_box",0x0202|0x0404,border_style.B_FANCY_BORDER)
		self.checksumbox=BBox(BRect(4,bounds.Height()/2+4,bounds.Width()-4,bounds.Height()-4),"checksum_box",0x0202|0x0404,border_style.B_FANCY_BORDER)
		self.AddChild(self.endianbox,None)
		self.AddChild(self.checksumbox,None)
		txt="Machine endianness: "+endianness
		font_height_value=font_height()
		self.GetFontHeight(font_height_value)
		r=BRect(4,4,self.StringWidth(txt)+8,font_height_value.ascent+8)
		self.sys_endian=BStringView(r,"sys_endianness",txt)
		self.endianbox.AddChild(self.sys_endian,None)
		txt="Save checksums in archives"
		self.ckb_savesum=BCheckBox(BRect(4,4,38+self.StringWidth(txt),font_height_value.ascent+8),"save_chksum",txt,BMessage(1600))
		txt="Check files upon extraction"
		self.ckb_checksum=BCheckBox(BRect(4,12+font_height_value.ascent,38+self.StringWidth(txt),16+font_height_value.ascent*2),"check_sum",txt,BMessage(1700))
		self.checksumbox.AddChild(self.ckb_savesum,None)
		self.checksumbox.AddChild(self.ckb_checksum,None)
		r = BRect(4,20+font_height_value.ascent*2,bounds.right-12,24+font_height_value.ascent*3)
		self.compr_lvl=BSlider(r,"cmpr_lvl","Compression level:",BMessage(1224),0,9)
		self.compr_lvl.SetHashMarks(hash_mark_location.B_HASH_MARKS_BOTH)
		self.compr_lvl.SetBarThickness(10.0)
		self.checksumbox.AddChild(self.compr_lvl,None)
		self.compr_lvl.SetLimitLabels("0","9")
		perc=BPath()
		find_directory(directory_which.B_USER_NONPACKAGED_DATA_DIRECTORY,perc,False,None)
		ent=BEntry(perc.Path()+"/HTPBZ2")
		if not ent.Exists():
			self.Close()
		else:
			ent.GetPath(perc)
			confile=BPath(perc.Path()+'/config.ini',None,False)
			ent=BEntry(confile.Path())
			if ent.Exists():
				Config.read(confile.Path())
				value=ConfigSectionMap("System")["savesum"]
				if value == "True":
					self.ckb_savesum.SetValue(1)
				else:
					self.ckb_savesum.SetValue(0)
				
				value=ConfigSectionMap("System")["checksum"]
				if value == "True":
					self.ckb_checksum.SetValue(1)
				else:
					self.ckb_checksum.SetValue(0)
				
				value=int(ConfigSectionMap("System")["compression"])
				self.compr_lvl.SetValue(value)
				
		

class SettingsWindow(BWindow):
	def __init__(self):
		BWindow.__init__(self, BRect(200,150,800,450), "Settings", window_type.B_FLOATING_WINDOW,  B_NOT_RESIZABLE|B_CLOSE_ON_ESCAPE)
		self.bckgnd = BView(self.Bounds(), "bckgnd_View", 8, 20000000)
		bckgnd_bounds=self.bckgnd.Bounds()
		self.AddChild(self.bckgnd,None)
		self.bckgnd.SetResizingMode(B_FOLLOW_ALL_SIDES)
		self.Options = ScrollView(BRect(4 , 4, bckgnd_bounds.Width()/2.5-4, bckgnd_bounds.Height()-4 ), 'OptionsScrollView')
		self.bckgnd.AddChild(self.Options.sv,None)
		self.box = BBox(BRect(bckgnd_bounds.Width()/2.5+2,2,bckgnd_bounds.Width()-2,bckgnd_bounds.Height()-2),"optionsbox",0x0202|0x0404,border_style.B_FANCY_BORDER)
		self.bckgnd.AddChild(self.box,None)
		perc=BPath()
		find_directory(directory_which.B_USER_NONPACKAGED_DATA_DIRECTORY,perc,False,None)
		ent=BEntry(perc.Path()+"/HTPBZ2")
		if not ent.Exists():
			self.Close()
		else:
			ent.GetPath(perc)
			confile=BPath(perc.Path()+'/config.ini',None,False)
			#self.confile=confile
			ent=BEntry(confile.Path())
			if ent.Exists():
				Config.read(confile.Path())
				sezione=Config.sections()
				for key in sezione:
					self.Options.lv.AddItem(BStringItem(key))
				self.Options.lv.AddItem(BStringItem("About"))
				
			else:
				saytxt="This should not happen: there's no config.ini!"
				alert= BAlert('Ops', saytxt, 'Ok', None,None,InterfaceDefs.B_WIDTH_AS_USUAL,alert_type.B_WARNING_ALERT)
				alert.Go()
				self.Close()
	def MessageReceived(self, msg):
		global save_hash,check_hash
		if msg.what == 54:
			son=self.box.CountChildren()
			if son>0:
				rmView=self.box.ChildAt(self.box.CountChildren()-1)
				rmView.Hide()
				rmView.RemoveSelf()
			if self.Options.lv.CurrentSelection()>-1:
				option=self.Options.lv.ItemAt(self.Options.lv.CurrentSelection()).Text()
				rec=self.box.Bounds()
				myrec=BRect(rec.left+4,rec.top+4,rec.right-4,rec.bottom-4)
				if option == "System":
					self.box.AddChild(SystemView(myrec),None)
				elif option == 'About':
					self.box.AddChild(AboutView(myrec),None)
		elif msg.what == 1600:
			self.rmView=self.box.ChildAt(self.box.CountChildren()-1)
			self.boxview=self.rmView.ChildAt(self.rmView.CountChildren()-1)
			self.bx=self.boxview.ChildAt(self.boxview.CountChildren()-3)
			perc=BPath()
			find_directory(directory_which.B_USER_NONPACKAGED_DATA_DIRECTORY,perc,False,None)
			ent=BEntry(perc.Path()+"/HTPBZ2")
			if not ent.Exists():
				self.Close()
			else:
				ent.GetPath(perc)
				confile=BPath(perc.Path()+'/config.ini',None,False)
				ent=BEntry(confile.Path())
				if ent.Exists():
					Config.read(confile.Path())
					cfgfile = open(confile.Path(),'w')
					if self.bx.Value():
						Config.set('System','savesum', "True")
						save_hash=True
					else:
						Config.set('System','savesum', "False")
						save_hash=False
					Config.write(cfgfile)
					cfgfile.close()
					Config.read(confile.Path())
		elif msg.what == 1700:
			self.rmView=self.box.ChildAt(self.box.CountChildren()-1)
			self.boxview=self.rmView.ChildAt(self.rmView.CountChildren()-1)
			self.bx=self.boxview.ChildAt(self.boxview.CountChildren()-2)
			perc=BPath()
			find_directory(directory_which.B_USER_NONPACKAGED_DATA_DIRECTORY,perc,False,None)
			ent=BEntry(perc.Path()+"/HTPBZ2")
			if not ent.Exists():
				self.Close()
			else:
				ent.GetPath(perc)
				confile=BPath(perc.Path()+'/config.ini',None,False)
				ent=BEntry(confile.Path())
				if ent.Exists():
					Config.read(confile.Path())
					cfgfile = open(confile.Path(),'w')
					if self.bx.Value():
						Config.set('System','checksum', "True")
						check_hash=True
					else:
						Config.set('System','checksum', "False")
						check_hash=False
					Config.write(cfgfile)
					cfgfile.close()
					Config.read(confile.Path())
		elif msg.what == 1224:
			self.rmView=self.box.ChildAt(self.box.CountChildren()-1)
			self.boxview=self.rmView.ChildAt(self.rmView.CountChildren()-1)
			self.slid=self.boxview.ChildAt(self.boxview.CountChildren()-1)
			perc=BPath()
			find_directory(directory_which.B_USER_NONPACKAGED_DATA_DIRECTORY,perc,False,None)
			ent=BEntry(perc.Path()+"/HTPBZ2")
			if not ent.Exists():
				self.Close()
			else:
				ent.GetPath(perc)
				confile=BPath(perc.Path()+'/config.ini',None,False)
				ent=BEntry(confile.Path())
				if ent.Exists():
					Config.read(confile.Path())
					cfgfile = open(confile.Path(),'w')
					Config.set('System','compression', str(self.slid.Value()))
					Config.write(cfgfile)
					cfgfile.close()
					Config.read(confile.Path())
	def FrameResized(self,x,y):
		self.ResizeTo(600,300)

class HTPBZ2Window(BWindow):
	opf=""
	tmpWind=[]
	def __init__(self,cmd,args):
		BWindow.__init__(self, BRect(200,170,800,278), "Tar Parallel-BZip2 Compressor/Decompressor with attributes", window_type.B_TITLED_WINDOW, B_NOT_RESIZABLE |B_QUIT_ON_WINDOW_CLOSE)
		self.bckgnd = BView(self.Bounds(), "bckgnd_View", 8, 20000000)
		rect=self.bckgnd.Bounds()
		self.AddChild(self.bckgnd,None)
		self.bckgnd.SetResizingMode(B_FOLLOW_ALL_SIDES)
		bckgnd_bounds=self.bckgnd.Bounds()
		self.box = BBox(BRect(0,0,bckgnd_bounds.Width(),bckgnd_bounds.Height()),"Underbox",0x0202|0x0404,border_style.B_FANCY_BORDER)
		self.bckgnd.AddChild(self.box, None)
		fon=BFont()
		font_height_value=font_height()
		self.bckgnd.GetFontHeight(font_height_value)
		self.rb1=BRadioButton(BRect(4,4,30+self.bckgnd.StringWidth("Compress"),font_height_value.ascent),"RB_Compres","Compress", BMessage(191))
		self.box.AddChild(self.rb1,None)
		self.rb2=BRadioButton(BRect(4,8+font_height_value.ascent,30+self.bckgnd.StringWidth("Decompress"),8+font_height_value.ascent*2),"RB_Decompres","Decompress", BMessage(181))
		self.box.AddChild(self.rb2,None)
		self.GoBtn=BButton(BRect(bckgnd_bounds.right-46,bckgnd_bounds.bottom-46,bckgnd_bounds.right-8,bckgnd_bounds.bottom-8),'GoBtn',"Go",BMessage(1024),B_FOLLOW_BOTTOM|B_FOLLOW_RIGHT)
		self.box.AddChild(self.GoBtn,None)
		self.OpenFP=BButton(BRect(40+self.bckgnd.StringWidth("Decompress"),8,40+self.bckgnd.StringWidth("Decompress")+32+self.bckgnd.StringWidth("Source"),46),"open_fp","Source",BMessage(207),B_FOLLOW_TOP|B_FOLLOW_LEFT)
		self.input=BTextControl(BRect(40+self.bckgnd.StringWidth("Decompress")+32+self.bckgnd.StringWidth("Source")+8,14,bckgnd_bounds.right-50,4+font_height_value.ascent*2),"text_input", "Files:","",BMessage(1800))
		self.input.SetDivider(self.bckgnd.StringWidth("Files: "))
		bf=BFont()
		bf.SetSize(24)
		self.SettingsBtn = BButton(BRect(bckgnd_bounds.right-46,8,bckgnd_bounds.right-8,46),"settings_btn","⚙",BMessage(407),B_FOLLOW_TOP|B_FOLLOW_RIGHT)
		self.box.AddChild(self.SettingsBtn,None)
		self.SettingsBtn.SetFont(bf)
		self.box.AddChild(self.OpenFP,None)
		self.SaveFP=BButton(BRect(8,bckgnd_bounds.bottom-46,32+self.bckgnd.StringWidth("To")+8,bckgnd_bounds.bottom-8),"save_fp","To",BMessage(307),B_FOLLOW_BOTTOM|B_FOLLOW_LEFT)
		self.box.AddChild(self.SaveFP,None)
		self.output=BTextControl(BRect(32+self.bckgnd.StringWidth("To")+16,bckgnd_bounds.bottom-40,bckgnd_bounds.right-50,bckgnd_bounds.bottom-8),"text_output", "target:","",BMessage(1900))
		self.output.SetDivider(self.bckgnd.StringWidth("target: "))
		self.box.AddChild(self.input,None)
		self.box.AddChild(self.output,None)
		self.fp=BFilePanel(B_SAVE_PANEL,None,None,0,False, None, None, True, True)
		print(type(node_flavor.B_DIRECTORY_NODE))
		self.ofp=BFilePanel(B_OPEN_PANEL,None,None,int(node_flavor.B_DIRECTORY_NODE)|int(node_flavor.B_FILE_NODE),True, None, None, True, True)
		self.autoload=""
		if args!=[]:
			for f in args:
				if self.autoload=="":
					self.autoload+=f
				else:
					self.autoload+=","+f
			self.input.SetText(self.autoload)
			if cmd=="c":
				self.rb1.SetValue(1)
				self.rb2.SetValue(0)
				self.list_autol=self.autoload.split(',')
				a=self.list_autol[0]
				open_file=os.path.basename(os.path.abspath(a))
				if BEntry(a).Exists():
					osdir=os.path.dirname(os.path.abspath(a))
					if len(self.list_autol)>1:
						osfile=os.path.basename(os.path.abspath(osdir))+".tar.bz2"
					else:
						osfile=os.path.basename(os.path.abspath(a))+".tar.bz2"
				else:
					osdir=os.getcwd()
					if len(self.list_autol)>1:
						osfile=os.path.basename(os.path.abspath(osdir))+".tar.bz2"
					else:
						osfile=os.path.basename(os.path.abspath(a))+".tar.bz2"
				self.output.SetText(osfile)
			elif cmd=="d":
				self.fp=BFilePanel(B_OPEN_PANEL,None,None,node_flavor.B_DIRECTORY_NODE,False, None, None, True, True)
				self.rb1.SetValue(0)
				self.rb2.SetValue(1)
				self.list_autol=self.autoload.split(',')
				open_file=os.path.basename(self.list_autol[0])
				osdir=os.path.dirname(self.list_autol[0])
				osfile=""
				osfileout=""
				for i in self.list_autol:
					if osfileout=="":
						if BEntry(i).Exists():
							osfileout=osdir
						else:
							osfileout=os.getcwd()
					else:
						if BEntry(i).Exists():
							osfileout+=","+osdir
						else:
							osfileout+=","+os.getcwd()
				self.output.SetText(osfileout)
#			ofpmsg=BMessage(45371)
#			ofpmsg.AddString("path",autoload)
#			be_app.WindowAt(0).PostMessage(ofpmsg)
#			osdir=os.path.dirname(autoload)
#			osfile=os.path.basename(autoload)
		else:
			osdir="/boot/home/Desktop"
			osfile="/boot/home/Desktop/output.tar.bz2"
		
		self.fp.SetPanelDirectory(osdir)
		self.fp.SetSaveText(osfile)
		
		self.ofp.SetPanelDirectory(osdir)
		self.ofp.SetSaveText(open_file)

	def MessageReceived(self, msg):
		if msg.what == 207:
			self.opf=""
			self.ofp.Show()
			
		elif msg.what == 307:
			self.fp.Show()
		elif msg.what == 407:
			self.settings_window = SettingsWindow()
			self.settings_window.Show()
		elif msg.what == 1024:
			self.list_autol=self.input.Text().split(",")
			if self.rb1.Value():
				create_compressed_archive(self.list_autol, self.output.Text())
			else:
				paths=self.input.Text().split(",")
				for path in paths:
					suf="".join(Path(path).suffixes)
					out=os.path.basename(path[:-len(suf)])
					decompress_archive(path, self.output.Text()+"/"+out)
		elif msg.what == 191:
			osdir="/boot/home/Desktop"
			osfile="/boot/home/Desktop/output.tar.bz2"
			self.fp=BFilePanel(B_SAVE_PANEL,None,None,0,False, None, None, True, True)
			self.fp.SetPanelDirectory(osdir)
			self.ofp.SetPanelDirectory(osdir)
			self.fp.SetSaveText("output.tar.bz2")
			self.input.SetText("")
			self.output.SetText("")
		elif msg.what == 181:
			osdir="/boot/home/Desktop"
			osfile="/boot/home/Desktop"
			self.fp=BFilePanel(B_OPEN_PANEL,None,None,node_flavor.B_DIRECTORY_NODE,False, None, None, True, True)
			self.fp.SetPanelDirectory(osdir)
			self.ofp.SetPanelDirectory(osdir)
		elif msg.what == 45371:
			percors=msg.FindString("path")
			if self.opf == "":
				self.opf="".join(percors)
			else:
				self.opf=self.opf+","+percors
			self.input.SetText(self.opf)
			self.list_autol=self.opf.split(",")
		elif msg.what == 1800:
			self.list_autol=self.input.Text().split(",")
	def QuitRequested(self):
		wnum = be_app.CountWindows()
		if wnum>1:
			if len(self.tmpWind)>0:
				for wind in self.tmpWind:
					wind.Lock()
					wind.Quit()
		return BWindow.QuitRequested(self)
		
def get_str_md5(txt):
	return hashlib.md5(txt.encode('utf-8')).hexdigest()

def get_bytes_md5(byt):
	return hashlib.md5(byt).hexdigest()

def get_endianness():
	global endianness
	packed = struct.pack('=I', 1)
	if packed[0] == 1:
		endianness='little'
	else:
		endianness='big'


def bytes_needed(value):
	if value==0:
		return 1
	else:
		numbytes = math.ceil(value.bit_length() / 8)
		if numbytes<=1:
			return 1
		elif numbytes<=2:
			return 2
		elif numbytes<=4:
			return 4
		else:
			return 8

def attr(node):
	al = []
	while 1:
		an = node.GetNextAttrName()
		if not an[1]:
			a = an[0]
		else:
			a = None
		if a is None:
			node.RewindAttrs()
			break
		else:
			pnfo = node.GetAttrInfo(a)
			if not pnfo[1]:
				nfo = pnfo[0]
			al.append((a,(nfo.type,nfo.size,node.ReadAttr(a, nfo.type, 0, None,nfo.size))))
	return al
	
def decompress_file(input_file, output_file, block_size=1024*1024):
	with bz2.BZ2File(input_file, 'rb') as f_in, open(output_file, 'wb') as f_out:
		while True:
			block = f_in.read(block_size)
			if not block:
				break
			f_out.write(block)

def get_type_string(value):
	type_string = struct.pack('>I', value).decode('utf-8')
	return type_string

def compress_block(block, compresslevel):
    return bz2.compress(block, compresslevel=compresslevel)

def parallel_compress_file(input_file, output_file, block_size=1024*1024, compresslevel=9):
    with open(input_file, 'rb') as f:
        blocks = []
        while True:
            block = f.read(block_size)
            if not block:
                break
            blocks.append(block)
    
    pool = multiprocessing.Pool()
    compress_partial = partial(compress_block, compresslevel=compresslevel)
    compressed_blocks = pool.map(compress_partial, blocks)
    pool.close()
    pool.join()

    with open(output_file, 'wb') as f:
        for compressed_block in compressed_blocks:
            f.write(compressed_block)

def extract_tar_with_attributes(tar_file, output_dir):
	global check_hash,endianness
	with tarfile.open(tar_file, "r") as tar:
		tar.extractall(output_dir)
		for member in tar.getmembers():
			if member.name.endswith('.attr'):
				attr_path = os.path.join(output_dir, member.name)
				original_file= attr_path[:-38] #Rimuove sia .attr che .{hash}
				with open(attr_path, 'r') as f:
					attr_data = json.load(f)
					for name, details in attr_data.items():
						attr_value = details['value']
						attr_type = details['type']
						attr_size = details['size']
						if check_hash:
							try:
								attr_hash = details['hash']
							except:
								check_hash=False
								#TODO: print to log missing hash on original_file, attribute name
						node=BNode(original_file)
						ck=get_type_string(details['type'])
						if ck == 'RAWT':
							attr_value = base64.b64decode(attr_value)
							if check_hash:
								if get_bytes_md5(attr_value)==attr_hash:
									print(original_file, name, "checksum OK")
								else:
									print(original_file, name, "checksum Failed")
						elif ck == 'LONG':
							attr_value = int(attr_value)
							attr_value = attr_value.to_bytes(4,byteorder=endianness)#'little')
							if check_hash:
								
								if get_bytes_md5(attr_value) == attr_hash:
									print(original_file, name, "checksum OK")
								else:
									print(original_file, name, "checksum Failed")
						elif ck == 'LLNG':
							attr_value = int(attr_value)
							attr_value = attr_value.to_bytes(8,byteorder=endianness)#'little')
							if check_hash:
								
								if get_bytes_md5(attr_value) == attr_hash:
									print(original_file, name, "checksum OK")
								else:
									print(original_file, name, "checksum Failed")
						elif ck == 'TIME':
							if check_hash:
								if get_bytes_md5(int(attr_value).to_bytes(8,byteorder=endianness))==attr_hash:#'little'))==attr_hash:
									print(original_file, name, "checksum OK")
								else:
									print(original_file, name, "checksum Failed")
							a=bytes_needed(attr_value)
							attr_value=attr_value.to_bytes(a,byteorder=endianness)#'little')
						elif ck == 'CSTR' or ck == 'MIMS':
							attr_value=str.encode(attr_value)
							if check_hash:
								if get_str_md5(attr_value)==attr_hash:
									print(original_file, name, "checksum OK")
								else:
									print(original_file, name, "checksum Failed")
							
						elif ck == 'BOOL':
							attr_value=bytes(attr_value,'utf-8')
							if check_hash:
								if get_bytes_md5(attr_value)==attr_hash:
									print(original_file, name, "checksum OK")
								else:
									print(original_file, name, "checksum Failed")
						elif ck == 'FLOT':
							attr_value=base64.b64decode(attr_value)
							if check_hash:
								if get_bytes_md5(attr_value)==attr_hash:
									print(original_file, name, "checksum OK")
								else:
									print(original_file, name, "checksum Failed")
						elif ck == 'DBLE':
							attr_value=base64.b64decode(attr_value)
							if check_hash:
								if get_bytes_md5(attr_value)==attr_hash:
									print(original_file, name, "checksum OK")
								else:
									print(original_file, name, "checksum Failed")
						else: #ripiego?
							attr_value = base64.b64decode(attr_value)
							if check_hash:
								if get_bytes_md5(attr_value)==attr_hash:
									print(original_file, name, "checksum OK")
								else:
									print(original_file, name, "checksum Failed")
						node.WriteAttr(name,attr_type,0,attr_value)
				os.remove(attr_path)

def add_attributes_to_tar(tar, path):
	global save_hash,endianness
	nf=BNode(path)
	attributes=attr(nf)
	if len(attributes)>0:
		attr_data = {}
		for name, (attr_type, attr_size, attr_value) in attributes:
			#print(name,get_type_string(attr_type))
			if get_type_string(attr_type)=='RAWT':
				if save_hash:
					attr_hash = get_bytes_md5(attr_value[0])
				attr_value = base64.b64encode(attr_value[0]).decode('utf-8')
			elif get_type_string(attr_type)=='TIME':
				if save_hash:
					attr_hash = get_bytes_md5(int(attr_value[0].timestamp()).to_bytes(8,byteorder=endianness))#'little'))
				attr_value=int(attr_value[0].timestamp())
			elif get_type_string(attr_type)=='CSTR':
				if save_hash:
					attr_hash = get_str_md5(attr_value[0])
				attr_value = attr_value[0]
			elif get_type_string(attr_type)=='BOOL':
				if save_hash:
					attr_hash = get_bytes_md5(struct.pack('?',attr_value[0]))
				attr_value = struct.pack('?',attr_value[0]).decode('utf-8')
			elif get_type_string(attr_type) =='LONG':
				if save_hash:
					endianed_bytes = attr_value[0].to_bytes(4,byteorder=endianness)#'little')
					attr_hash = get_bytes_md5(endianed_bytes)
				attr_value = str(attr_value[0])
			elif get_type_string(attr_type) =='LLNG':
				if save_hash:
					endianed_bytes = attr_value[0].to_bytes(8,byteorder=endianness)#'little')
					attr_hash = get_bytes_md5(endianed_bytes)
				attr_value = str(attr_value[0])
			elif get_type_string(attr_type)=='FLOT':
				Battr_value=struct.pack('<f',attr_value[0])
				if save_hash:
					attr_hash = get_bytes_md5(Battr_value)
				attr_value = base64.b64encode(Battr_value).decode('utf-8')
			elif get_type_string(attr_type)=='DBLE':
				Battr_value=struct.pack('<d',attr_value[0])
				if save_hash:
					attr_hash = get_bytes_md5(Battr_value)
				attr_value = base64.b64encode(Battr_value).decode('utf-8')
			elif get_type_string(attr_type)=='MIMS':
				if save_hash:
					attr_hash = get_str_md5(attr_value[0])
				attr_value = attr_value[0]
			else: #ripiego
				if isinstance(attr_value[0],str):
					if save_hash:
						attr_hash = get_str_md5(attr_value[0])
					attr_value = attr_value[0]
				elif isinstance(attr_value[0],int):
					if save_hash:
						numb = bytes_needed(attr_value[0])
						endianed_bytes = attr_value[0].to_bytes(numb,byteorder=endianness)
						attr_hash = get_bytes_md5(endianed_bytes)
					attr_value = str(attr_value[0])
				elif isinstance(attr_value[0],float):
					Battr_value=struct.pack('<f',attr_value[0])
					if save_hash:
						attr_hash = get_bytes_md5(Battr_value)
					attr_value = str(Battr_value)
				#elif isinstance(attr_value[0],double): # there's no double in python
				#	Battr_value=struct.pack('<d',attr_value[0])
				#	if save_hash:
				#		attr_hash = get_bytes_md5(Battr_value)
				#	attr_value = str(Battr_value)
				else:
					if save_hash:
						attr_hash = get_bytes_md5(attr_value[0])
					attr_value = base64.b64encode(attr_value[0]).decode('utf-8')
			if save_hash:
				attr_data[name] = {
					'type': attr_type,
					'size': attr_size,
					'value': attr_value,
					'hash': attr_hash
				}
			else:
				attr_data[name] = {
					'type': attr_type,
					'size': attr_size,
					'value': attr_value
				}
		attr_json = json.dumps(attr_data).encode('utf-8')
		md5attr_json=str(get_bytes_md5(attr_json))
		print(md5attr_json)#TODO: Check on extract this checksum
		attr_info = tarfile.TarInfo(name=f"{path}.{md5attr_json}.attr")
		attr_info.size = len(attr_json)
		tar.addfile(attr_info, io.BytesIO(attr_json))

def create_tar_with_attributes(input_paths, tar_file):
	with tarfile.open(tar_file, "w") as tar:
		for input_path in input_paths:
			tar.add(input_path, arcname=os.path.basename(input_path))
			if os.path.isfile(input_path):
				add_attributes_to_tar(tar, input_path)
			elif os.path.isdir(input_path):
				add_attributes_to_tar(tar,input_path)
				for root, _, files in os.walk(input_path):
					for dir in _:
						dir_path = os.path.join(root,dir)
						#tar.add(dir_path, arcname=os.path.relpath(dir_path, start=input_path))
						add_attributes_to_tar(tar,dir_path)
					for file in files:
						file_path = os.path.join(root, file)
						#tar.add(file_path, arcname=os.path.relpath(file_path, start=input_path))
						add_attributes_to_tar(tar, file_path)

def create_compressed_archive(input_paths, output_file, block_size=1024*1024, compresslevel=9):
    tar_file = output_file + '.tar'
    create_tar_with_attributes(input_paths, tar_file)
    parallel_compress_file(tar_file, output_file, block_size, compresslevel)
    os.remove(tar_file)

def decompress_archive(input_file, output_dir, block_size=1024*1024):
    tar_file = input_file + '.tar'
    decompress_file(input_file, tar_file, block_size)
    extract_tar_with_attributes(tar_file, output_dir)
    os.remove(tar_file)

class App(BApplication):
	def __init__(self):
		BApplication.__init__(self, "application/x-python-HTPBZ2")
		self.realargs=[]
		self.cmd=""
	def ReadyToRun(self):
		self.window = HTPBZ2Window(self.cmd,self.realargs)
		self.window.Show()
	def ArgvReceived(self,num,args):
		with open('testargvreceived.txt', 'w') as writer:
			writer.write(str(args))
		realargs=args
		if args[1][-9:]=="HTPBZ2.py":
			realargs.pop(1)
			realargs.pop(0)
			if len(realargs)>1:
				if len(realargs[0])==2:
					if realargs[0][0]=="-" and realargs[0][1] in ["c","d"]:
						self.cmd=realargs[0][1]
						realargs.pop(0)
						self.realargs=realargs
		#self.autoload=args[-1]# argvReceived is executed before readytorun, we pass the last argument
	def RefsReceived(self, msg):
		if msg.what == B_REFS_RECEIVED:
			i = 0
			while True:
				try:
					bitul=False
					er = entry_ref()
					rito=msg.FindRef("refs", i,er)
					entry = BEntry(er,True)
					if entry.Exists():
						percors=BPath()
						entry.GetPath(percors)
						#print("da RefsReceived",percors.Path())
						ofpmsg=BMessage(45371)
						ofpmsg.AddString("path",percors.Path())
						be_app.WindowAt(0).PostMessage(ofpmsg)
					else:
						break
				except:
					bitul=True
				if bitul:
					break
				i+=1
		BApplication.RefsReceived(self,msg)

	def MessageReceived(self,msg):
		if msg.what == B_SAVE_REQUESTED:
			e = msg.FindString("name")
			messaggio = BMessage(54173)
			messaggio.AddString("name",e)
			be_app.WindowAt(0).PostMessage(messaggio)
			return
#		elif msg.what == B_ARGV_RECEIVED:
#			self.asku=BAlert('cle', "ricevuto argv", 'Ok', None,None,InterfaceDefs.B_WIDTH_AS_USUAL,alert_type.B_STOP_ALERT)
#			self.asku.Go()
		BApplication.MessageReceived(self,msg)
#	def MessageReceived(self,msg):
#		msg.PrintToStream()
#		BApplication.MessageReceived(self,msg)

#	def Pulse(self):
#		if self.window.enabletimer:
#			be_app.WindowAt(0).PostMessage(BMessage(66))


def main():
    global be_app
    be_app = App()
    be_app.Run()
	
if __name__ == "__main__":
	global save_hash,check_hash,endianness
	perc=BPath()
	find_directory(directory_which.B_USER_NONPACKAGED_DATA_DIRECTORY,perc,False,None)
	datapath=BDirectory(perc.Path()+"/HTPBZ2")
	ent=BEntry(datapath,perc.Path()+"/HTPBZ2")
	if not ent.Exists():
		datapath.CreateDirectory(perc.Path()+"/HTPBZ2", datapath)
	ent.GetPath(perc)
	confile=BPath(perc.Path()+'/config.ini',None,False)
	ent=BEntry(confile.Path())
	if ent.Exists():
		Config.read(confile.Path())
		#sezione=Config.sections()
		for key in Config["System"]:
			if key == "endianness":
				endianness = ConfigSectionMap("System")["endianness"]
			elif key == "checksum":
				value = ConfigSectionMap("System")["checksum"]
				if value == "True":
					check_hash=True
				else:
					check_hash=False
			elif key == "savesum":
				value = ConfigSectionMap("System")["savesum"]
				if value == "True":
					save_hash=True
				else:
					save_hash=False
	else:
		cfgfile = open(confile.Path(),'w')
		Config.add_section('System')
		get_endianness()
		Config.set('System','endianness', endianness)
		Config.set('System','checksum', "False")
		check_hash=False
		Config.set('System','savesum', "False")
		Config.set('System','compression', "9")
		save_hash=False
		Config.write(cfgfile)
		cfgfile.close()
		Config.read(confile.Path())
	
	main()