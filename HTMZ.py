#!/boot/system/bin/python3
import os,sys,tarfile,bz2,io,base64,struct,math,hashlib,json,configparser,time,multiprocessing#,datetime,
from functools import partial
import concurrent.futures
from Be import BApplication, BWindow, BView, BNode,BRadioButton,BButton,BMessage, window_type, B_NOT_RESIZABLE, B_CLOSE_ON_ESCAPE, B_QUIT_ON_WINDOW_CLOSE, BTextControl, BAlert,BListView, BScrollView,BStringItem,BTextView,BRect, BBox, BFont, InterfaceDefs, BPath, BDirectory, BEntry, BStringView, BSlider, BMenu, BMenuField, BMenuItem, BFile, BCheckBox, AppDefs, BScreen,BListItem
from Be.FindDirectory import *
from Be.Alert import alert_type
from Be.InterfaceDefs import border_style,orientation,B_CONTROL_KEY
from Be.ListView import list_view_type
from Be.AppDefs import *
from Be.View import *
from Be.GraphicsDefs import *
from Be.FilePanel import *
from Be.Application import *
from Be.Font import font_height,B_OUTLINED_FACE,B_ITALIC_FACE,be_plain_font, be_bold_font
from Be.Entry import entry_ref, get_ref_for_path
from Be.StorageDefs import node_flavor
from Be.Slider import hash_mark_location
from Be.TypeConstants import *
from pathlib import Path
from threading import Thread
import subprocess

Config=configparser.ConfigParser()
global ver,status,rev
ver="1"
status="beta"
rev="20240824"
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
	def __init__(self, rect, name,vsb=False):
		self.lv = BListView(rect, name, list_view_type.B_SINGLE_SELECTION_LIST)
		self.lv.SetResizingMode(B_FOLLOW_TOP_BOTTOM)
		self.lv.SetSelectionMessage(BMessage(self.SectionSelection))
		self.lv.SetInvocationMessage(BMessage(self.HiWhat))
		self.sv = BScrollView(name, self.lv,B_FOLLOW_NONE,0,False,vsb,border_style.B_FANCY_BORDER)
		self.sv.SetResizingMode(B_FOLLOW_TOP_BOTTOM)

def read_config_file():
	perc=BPath()
	find_directory(directory_which.B_USER_NONPACKAGED_DATA_DIRECTORY,perc,False,None)
	ent=BEntry(perc.Path()+"/HTPBZ2")
	if not ent.Exists():
		return(False,None)
	else:
		ent.GetPath(perc)
		confile=BPath(perc.Path()+'/config.ini',None,False)
		return(True,confile)
		

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
		txt="TMZ a Tar-ParallelBZip2 format"
		txtw=fon.StringWidth(txt)
		r=BRect(bounds.Width()/2-txtw/2-4,4,bounds.Width()/2+txtw/2+4,font_height_value.ascent+4)
		self.name=BStringView(r,"app_name",txt)
		self.name.SetFont(fon)
		self.name.SetHighColor(255,0,0,0)
		self.AddChild(self.name,None)
		txt="This simple utility compresses and decompresses files and folders in a tar.bz2 format, and also adds Haiku-specific attributes to the archive.\nCompression can be parallelized and elaborated in ram (and attributes extraction too)."
		abrect=BRect(4,font_height_value.ascent+8, bounds.Width()-4,bounds.Height()/2-4)
		inner_ab=BRect(4,4,abrect.Width()-4,abrect.Height()-4)
		self.AboutText = BTextView(abrect, 'aBOUTTxTView', inner_ab , B_FOLLOW_NONE)
		self.AboutText.MakeEditable(False)
		self.AboutText.MakeSelectable(False)
		fon1=BFont(be_plain_font)
		fon1.SetSize(13.0)
		col1=rgb_color()
		col1.red=10
		col1.green=200
		col1.blue=10
		col1.alpha=200
		self.AboutText.SetFontAndColor(fon1,B_FONT_ALL,col1)
		self.AboutText.SetText(txt,None)
		self.AddChild(self.AboutText,None)
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
		r = BRect(bounds.Width()*2/3-16,bounds.Height()/2+8,fon.StringWidth(txt)+bounds.Width()*2/3,bounds.Height()-4)
		self.author=BStringView(r,"app_auth",txt)
		self.author.SetFont(fon)
		self.AddChild(self.author,None)

class CompressView(BView):
	def __init__(self,frame):
		global cmplvl,save_hash,block_size,cinram,cparallelization
		BView.__init__(self,frame,"Compression",8,20000000)
		bounds=self.Bounds()
		self.checksumbox=BBox(BRect(4,4,bounds.Width()-4,bounds.Height()-4),"checksum_box",0x0202|0x0404,border_style.B_FANCY_BORDER)
		self.AddChild(self.checksumbox,None)
		chkb_bounds=self.checksumbox.Bounds()
		font_height_value=font_height()
		fon=BFont()
		fon.SetSize(32)
		fon_height_value=font_height()
		self.GetFontHeight(fon_height_value)
		r=BRect(chkb_bounds.right-8-fon.StringWidth("0"),24+fon.Size()*2,chkb_bounds.right-4,28+fon.Size()*3)
		self.cmplvl_value = BStringView(r,"cmplvl_value","9")
		self.cmplvl_value.SetFont(fon)
		self.checksumbox.AddChild(self.cmplvl_value,None)
		txt="Save checksums in archives"
		self.ckb_savesum=BCheckBox(BRect(4,4,38+self.StringWidth(txt),font_height_value.ascent+8),"save_chksum",txt,BMessage(1600))
		self.checksumbox.AddChild(self.ckb_savesum,None)
		r=BRect(4,fon.Size()+12,bounds.right-12,fon.Size()*2+20)
		self.BlkSz=BTextControl(r,"block_size_txt","Block size:",str(block_size),BMessage(1324))
		self.checksumbox.AddChild(self.BlkSz,None)
		
		r = BRect(4,32+fon.Size()*3,bounds.right-12,36+fon.Size()*4)
		self.compr_lvl=BSlider(r,"cmpr_lvl","Compression level:",BMessage(1224),1,9)
		self.compr_lvl.SetHashMarks(hash_mark_location.B_HASH_MARKS_BOTH)
		self.compr_lvl.SetBarThickness(10.0)
		self.checksumbox.AddChild(self.compr_lvl,None)
		self.compr_lvl.SetLimitLabels("1","9")
		
		uwu=self.StringWidth("Tar management:")+10
		d={150:"use more resources",152:"let tar handle"}
		self.menup=BMenu("Management")
		self.menup.SetLabelFromMarked(True)
		for k in d.keys():
			self.menup.AddItem(BMenuItem(d[k], BMessage(k),d[k][0],B_CONTROL_KEY))
		self.pbar = BMenuField(BRect(10, chkb_bounds.bottom-fon.Size()*2-4, chkb_bounds.Width()-8, chkb_bounds.bottom-fon.Size()-4), 'pop1', 'Tar management:', self.menup,B_FOLLOW_TOP)
		self.pbar.SetDivider(uwu)
		self.checksumbox.AddChild(self.pbar,None)
		for k in d.keys():
			if k-150==cparallelization:
				itm=self.menup.FindItem(d[k])
				itm.SetMarked(True)
		txt="Compress in ram"
		self.ckb_cinram=BCheckBox(BRect(4,chkb_bounds.bottom-fon.Size()-4,38+self.StringWidth(txt),chkb_bounds.bottom-4),"chkbox_compress_inram",txt,BMessage(1500))
		self.checksumbox.AddChild(self.ckb_cinram,None)
		ck=read_config_file()
		if ck[0]:
			confile=ck[1]
			ent=BEntry(confile.Path())
			if ent.Exists():
				Config.read(confile.Path())
				value=ConfigSectionMap("Compression")["savesum"]
				if value == "True":
					self.ckb_savesum.SetValue(1)
				else:
					self.ckb_savesum.SetValue(0)
				value=ConfigSectionMap("Compression")["cinram"]
				if value == "True":
					self.ckb_cinram.SetValue(1)
				else:
					self.ckb_cinram.SetValue(0)
				strvalue=ConfigSectionMap("Compression")["compression"]
				value=int(strvalue)
				self.compr_lvl.SetValue(value)
				self.cmplvl_value.SetText(strvalue)
				strvalue=ConfigSectionMap("Compression")["block_size"]
		else:
			self.close()
		if cparallelization==2:
			self.ckb_cinram.SetEnabled(0)
		else:
			self.ckb_cinram.SetEnabled(1)
		
class DecompressView(BView):
	def __init__(self,frame):
		global parallelization,check_hash,inram,experimental
		BView.__init__(self,frame,"Decompression",8,20000000)
		bounds=self.Bounds()
		self.checksumbox=BBox(BRect(4,4,bounds.Width()-4,bounds.Height()-4),"checksum_box",0x0202|0x0404,border_style.B_FANCY_BORDER)
		self.AddChild(self.checksumbox,None)
		chkb_bounds=self.checksumbox.Bounds()
		font_height_value=font_height()
		fon=BFont()
		fon_height_value=font_height()
		self.GetFontHeight(fon_height_value)
		txt="Check files on extraction"
		self.ckb_checksum=BCheckBox(BRect(4,4,38+self.StringWidth(txt),8+fon.Size()),"check_sum",txt,BMessage(1700))
		self.checksumbox.AddChild(self.ckb_checksum,None)
		uwu=self.StringWidth("Tar management:")+10
		if experimental:
			# 101,103 produce different output folders in size still trying to figure out the reasons
			d={100:"Multi-threading",101:"Batched multithreading",102:"Serial standalone",103:"Single thread"}
		else:
			# notes:
			# 100: uses a serial bz2 extraction, then a serial tar.extractall and a multithreaded attributes writing
			# 102: it lets tar handle the whole tar.bz2 (tmz) archive and then a single thread attributes writing
			d={100:"use more resources",102:"let tar handle"}
		self.menup=BMenu("Management")
		self.menup.SetLabelFromMarked(True)
		for k in d.keys():
			self.menup.AddItem(BMenuItem(d[k], BMessage(k),d[k][0],B_CONTROL_KEY))
		self.pbar = BMenuField(BRect(10, 28+fon.Size()*2, chkb_bounds.Width()-8, 32+3*fon.Size()), 'pop1', 'Tar management:', self.menup,B_FOLLOW_TOP)
		self.pbar.SetDivider(uwu)
		self.checksumbox.AddChild(self.pbar,None)
		for k in d.keys():
			if k-100==parallelization:
				itm=self.menup.FindItem(d[k])
				itm.SetMarked(True)
		txt="Extract BZip2 in ram"
		self.inramckbox = BCheckBox(BRect(4,80+3*fon.Size(),38+self.StringWidth(txt),84+4*fon.Size()),"check_sum",txt,BMessage(1400))
		self.checksumbox.AddChild(self.inramckbox,None)
		self.inramckbox.SetValue(inram)
		if parallelization==2:
			self.inramckbox.SetEnabled(0)
		else:
			self.inramckbox.SetEnabled(1)
		self.ckb_checksum.SetValue(check_hash)

class CpuStringView(BStringView):
	def __init__(self,frame,name,value,max):
		self.value=value
		self.max=max
		label=str(value)+"/"+str(max)
		BStringView.__init__(self,frame,name,label)
	def SetValue(self,value):
		self.value=value
		label=str(value)+"/"+str(self.max)
		self.SetText(label)
	def ThisIsMe(self):
		return True
		
class SystemView(BView):
	def __init__(self,frame):
		global endianness,num_cpus
		BView.__init__(self,frame,"About",8,20000000)
		bounds=self.Bounds()
		self.endianbox=BBox(BRect(4,4,bounds.Width()-4,bounds.Height()-4),"endianess_box",0x0202|0x0404,border_style.B_FANCY_BORDER)
		self.AddChild(self.endianbox,None)
		txt="Machine endianness: "+endianness
		font_height_value=font_height()
		self.GetFontHeight(font_height_value)
		r=BRect(4,4,self.StringWidth(txt)+8,font_height_value.ascent+8)
		self.sys_endian=BStringView(r,"sys_endianness",txt)
		self.endianbox.AddChild(self.sys_endian,None)
		txt="CPUs used for de/compression:"
		r=BRect(4,12+font_height_value.ascent,self.StringWidth(txt)+8,20+font_height_value.ascent*2)
		self.workers=BStringView(r,"cpu_workers",txt)
		self.endianbox.AddChild(self.workers,None)
		r=BRect(self.StringWidth(txt)+20,12+font_height_value.ascent,bounds.right-12,20+font_height_value.ascent*2)
		self.cpus_value=CpuStringView(r,"cpus_value",num_cpus,multiprocessing.cpu_count())
		self.endianbox.AddChild(self.cpus_value,None)
		r = BRect(4,24+font_height_value.ascent*2,bounds.right-12,32+font_height_value.ascent*3)
		self.numcpus=BSlider(r,"num_cpus","Number of CPUs to be used:",BMessage(4221),1,multiprocessing.cpu_count())
		self.numcpus.SetHashMarks(hash_mark_location.B_HASH_MARKS_BOTH)
		self.numcpus.SetBarThickness(10.0)
		self.endianbox.AddChild(self.numcpus,None)
		self.numcpus.SetLimitLabels("1",str(multiprocessing.cpu_count()))
		self.numcpus.SetValue(num_cpus)
				
class SettingsWindow(BWindow):
	def __init__(self):
		global alerts
		BWindow.__init__(self, BRect(200,150,800,450), "Settings", window_type.B_FLOATING_WINDOW,  B_NOT_RESIZABLE|B_CLOSE_ON_ESCAPE)
		self.bckgnd = BView(self.Bounds(), "bckgnd_View", 8, 20000000)
		bckgnd_bounds=self.bckgnd.Bounds()
		self.AddChild(self.bckgnd,None)
		self.bckgnd.SetResizingMode(B_FOLLOW_ALL_SIDES)
		self.Options = ScrollView(BRect(4 , 4, bckgnd_bounds.Width()/2.5-4, bckgnd_bounds.Height()-4 ), 'OptionsScrollView')
		self.bckgnd.AddChild(self.Options.sv,None)
		self.box = BBox(BRect(bckgnd_bounds.Width()/2.5+2,2,bckgnd_bounds.Width()-2,bckgnd_bounds.Height()-2),"optionsbox",0x0202|0x0404,border_style.B_FANCY_BORDER)
		self.bckgnd.AddChild(self.box,None)
		ck=read_config_file()
		if ck[0]:
			confile=ck[1]
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
				alerts.append(alert)
				alert.Go()
				self.Close()
		else:
			self.Close()
	def set_cthreadization(self,mw):
			global cparallelization
			self.rmView=self.box.ChildAt(self.box.CountChildren()-1)
			self.boxview=self.rmView.ChildAt(self.rmView.CountChildren()-1)
			a=self.boxview.ChildAt(0)
			endof=False
			while True:
				if type(a)==BCheckBox:
					if a.Label() == "Compress in ram":
						if mw==152:
							a.SetEnabled(0)
						else:
							a.SetEnabled(1)
						break
				a=a.NextSibling()
				if a == None:
					endof=True
					break
			if endof:
				saytxt="Handling wrong configuration, ignoring"
				alert= BAlert('Ops', saytxt, 'Ok', None,None,InterfaceDefs.B_WIDTH_AS_USUAL,alert_type.B_WARNING_ALERT)
				alerts.append(alert)
				alert.Go()
				return
			ck=read_config_file()
			if ck[0]:
				confile=ck[1]
				ent=BEntry(confile.Path())
				if ent.Exists():
					Config.read(confile.Path())
					cfgfile = open(confile.Path(),'w')
					cparallelization=mw-150
					Config.set('Compression','cparallelization', str(cparallelization))
					Config.write(cfgfile)
					cfgfile.close()
					Config.read(confile.Path())
			else:
				self.Close()
	def set_threadization(self,mw):
			global parallelization
			self.rmView=self.box.ChildAt(self.box.CountChildren()-1)
			self.boxview=self.rmView.ChildAt(self.rmView.CountChildren()-1)
			a=self.boxview.ChildAt(0)
			endof=False
			while True:
				if type(a)==BCheckBox:
					if a.Label() == "Extract BZip2 in ram":
						if mw==102:
							a.SetEnabled(0)
						else:
							a.SetEnabled(1)
						break
				a=a.NextSibling()
				if a == None:
					endof=True
					break
			if endof:
				saytxt="Handling wrong configuration, ignoring"
				alert= BAlert('Ops', saytxt, 'Ok', None,None,InterfaceDefs.B_WIDTH_AS_USUAL,alert_type.B_WARNING_ALERT)
				alerts.append(alert)
				alert.Go()
				return
			ck=read_config_file()
			if ck[0]:
				confile=ck[1]
				ent=BEntry(confile.Path())
				if ent.Exists():
					Config.read(confile.Path())
					cfgfile = open(confile.Path(),'w')
					parallelization=mw-100
					Config.set('Decompression','parallelization', str(parallelization))
					Config.write(cfgfile)
					cfgfile.close()
					Config.read(confile.Path())
			else:
				self.Close()
					
	def MessageReceived(self, msg):
		global save_hash,check_hash,num_cpus,block_size,opt_view,inram,alerts
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
					opt_view=SystemView(myrec)
					self.box.AddChild(opt_view,None)
				elif option == "Compression":
					opt_view=CompressView(myrec)
					self.box.AddChild(opt_view,None)
				elif option == "Decompression":
					opt_view=DecompressView(myrec)
					self.box.AddChild(opt_view,None)
				elif option == 'About':
					opt_view=AboutView(myrec)
					self.box.AddChild(opt_view,None)
		elif msg.what in [100,101,102,103]:
			self.set_threadization(msg.what)
		elif msg.what in [150,152]:
			self.set_cthreadization(msg.what)
		elif msg.what == 1400:
			self.rmView=self.box.ChildAt(self.box.CountChildren()-1)
			self.boxview=self.rmView.ChildAt(self.rmView.CountChildren()-1)
			a=self.boxview.ChildAt(0)
			endof=False
			while True:
				if type(a)==BCheckBox:
					if a.Label() == "Extract BZip2 in ram":
						break
				a=a.NextSibling()
				if a == None:
					endof=True
					break
			if endof:
				saytxt="Handling wrong configuration, ignoring"
				alert= BAlert('Ops', saytxt, 'Ok', None,None,InterfaceDefs.B_WIDTH_AS_USUAL,alert_type.B_WARNING_ALERT)
				alerts.append(alert)
				alert.Go()
				return
			ck=read_config_file()
			if ck[0]:
				confile=ck[1]
				ent=BEntry(confile.Path())
				if ent.Exists():
					Config.read(confile.Path())
					cfgfile = open(confile.Path(),'w')
					if a.Value():
						Config.set('Decompression','inram', "True")
						inram=True
					else:
						Config.set('Decompression','inram', "False")
						inram=False
					Config.write(cfgfile)
					cfgfile.close()
					Config.read(confile.Path())
			else:
				self.Close()
		elif msg.what == 1500:
			self.rmView=self.box.ChildAt(self.box.CountChildren()-1)
			self.boxview=self.rmView.ChildAt(self.rmView.CountChildren()-1)
			a=self.boxview.ChildAt(0)
			endof=False
			while True:
				if type(a)==BCheckBox:
					if a.Label()=="Compress in ram":
						break
				a=a.NextSibling()
				if a == None:
					endof=True
					break
			if endof:
				saytxt="Handling wrong configuration, ignoring"
				alrt= BAlert('Ops', saytxt, 'Ok', None,None,InterfaceDefs.B_WIDTH_AS_USUAL,alert_type.B_WARNING_ALERT)
				alerts.append(alrt)
				alrt.Go()
				return
			ck=read_config_file()
			if ck[0]:
				confile=ck[1]
				ent=BEntry(confile.Path())
				if ent.Exists():
					Config.read(confile.Path())
					cfgfile = open(confile.Path(),'w')
					if a.Value():
						Config.set('Compression','cinram', "True")
						cinram=True
					else:
						Config.set('Compression','cinram', "False")
						cinram=False
					Config.write(cfgfile)
					cfgfile.close()
					Config.read(confile.Path())
			else:
				self.Close()
		elif msg.what == 1600:
			self.rmView=self.box.ChildAt(self.box.CountChildren()-1)
			self.boxview=self.rmView.ChildAt(self.rmView.CountChildren()-1)
			a=self.boxview.ChildAt(0)
			endof=False
			while True:
				if type(a)==BCheckBox:
					if a.Label()=="Save checksums in archives":
						break
				a=a.NextSibling()
				if a == None:
					endof=True
					break
			if endof:
				saytxt="Handling wrong configuration, ignoring"
				alrt= BAlert('Ops', saytxt, 'Ok', None,None,InterfaceDefs.B_WIDTH_AS_USUAL,alert_type.B_WARNING_ALERT)
				alerts.append(alrt)
				alrt.Go()
				return
			ck=read_config_file()
			if ck[0]:
				confile=ck[1]
				ent=BEntry(confile.Path())
				if ent.Exists():
					Config.read(confile.Path())
					cfgfile = open(confile.Path(),'w')
					if a.Value():
						Config.set('Compression','savesum', "True")
						save_hash=True
					else:
						Config.set('Compression','savesum', "False")
						save_hash=False
					Config.write(cfgfile)
					cfgfile.close()
					Config.read(confile.Path())
			else:
				self.Close()
		elif msg.what == 1700:
			self.rmView=self.box.ChildAt(self.box.CountChildren()-1)
			self.boxview=self.rmView.ChildAt(self.rmView.CountChildren()-1)
			a=self.boxview.ChildAt(0)
			endof=False
			while True:
				if type(a)==BCheckBox:
					if a.Label()=="Check files on extraction":
						break
				a=a.NextSibling()
				if a == None:
					endof=True
					break
			if endof:
				saytxt="Handling wrong configuration, ignoring"
				alrt= BAlert('Ops', saytxt, 'Ok', None,None,InterfaceDefs.B_WIDTH_AS_USUAL,alert_type.B_WARNING_ALERT)
				alerts.append(alrt)
				alrt.Go()
				return
			ck=read_config_file()
			if ck[0]:
				confile=ck[1]
				ent=BEntry(confile.Path())
				if ent.Exists():
					Config.read(confile.Path())
					cfgfile = open(confile.Path(),'w')
					if a.Value():
						Config.set('Decompression','checksum', "True")
						check_hash=True
					else:
						Config.set('Decompression','checksum', "False")
						check_hash=False
					Config.write(cfgfile)
					cfgfile.close()
					Config.read(confile.Path())
			else:
				self.Close()
		elif msg.what == 1324:
			self.rmView=self.box.ChildAt(self.box.CountChildren()-1)
			self.boxview=self.rmView.ChildAt(self.rmView.CountChildren()-1)
			a=self.boxview.ChildAt(0)
			endof=False
			while True:
				if type(a)==BTextControl:
					break
				a=a.NextSibling()
				if a == None:
					endof=True
					break
			if endof:
				saytxt="Handling wrong configuration, ignoring"
				alrt= BAlert('Ops', saytxt, 'Ok', None,None,InterfaceDefs.B_WIDTH_AS_USUAL,alert_type.B_WARNING_ALERT)
				alerts.append(alrt)
				alrt.Go()
				return
			try:
				v=int(a.Text())
			except:
				saytxt="Value not suitable for block size"
				alrt= BAlert('Ops', saytxt, 'Ok', None,None,InterfaceDefs.B_WIDTH_AS_USUAL,alert_type.B_STOP_ALERT)
				alerts.append(alrt)
				alrt.Go()
				return
			ck=read_config_file()
			if ck[0]:
				confile=ck[1]
				ent=BEntry(confile.Path())
				if ent.Exists():
					Config.read(confile.Path())
					cfgfile = open(confile.Path(),'w')
					Config.set('Compression','block_size', str(v))
					Config.write(cfgfile)
					cfgfile.close()
					Config.read(confile.Path())
					block_size=v
			else:
				self.Close()
		elif msg.what == 4221:
			self.rmView=self.box.ChildAt(self.box.CountChildren()-1)
			self.boxview=self.rmView.ChildAt(self.rmView.CountChildren()-1)
			a=self.boxview.ChildAt(0)
			endof=False
			while True:
				if type(a)==BSlider:
					self.slid=a
					break
				a=a.NextSibling()
				if a == None:
					endof=True
					break
			if endof:
				saytxt="Handling wrong configuration, ignoring"
				alert= BAlert('Ops', saytxt, 'Ok', None,None,InterfaceDefs.B_WIDTH_AS_USUAL,alert_type.B_WARNING_ALERT)
				alerts.append(alert)
				alert.Go()
				return
			a=self.boxview.ChildAt(0)
			num_cpus=self.slid.Value()
			endof=False
			while True:
				#if "/" in a.Text():
				try:
					if a.ThisIsMe():
						break
				except:
					pass
				a=a.NextSibling()
				if a == None:
					endof=True
					break
			self.cpus_value=a
			if endof:
				saytxt="Handling wrong configuration, ignoring"
				alrt= BAlert('Ops', saytxt, 'Ok', None,None,InterfaceDefs.B_WIDTH_AS_USUAL,alert_type.B_WARNING_ALERT)
				alerts.append(alrt)
				alrt.Go()
				return
			ck=read_config_file()
			if ck[0]:
				confile=ck[1]
				v=self.slid.Value()
				ent=BEntry(confile.Path())
				if ent.Exists():
					Config.read(confile.Path())
					cfgfile = open(confile.Path(),'w')
					Config.set('System','cpus', str(v))
					Config.write(cfgfile)
					cfgfile.close()
					Config.read(confile.Path())
					self.cpus_value.SetValue(v)
			else:
				self.Close()
		elif msg.what == 1224:
			self.rmView=self.box.ChildAt(self.box.CountChildren()-1)
			self.boxview=self.rmView.ChildAt(self.rmView.CountChildren()-1)
			a=self.boxview.ChildAt(0)
			endof=False
			while True:
				if type(a)==BSlider:
					self.slid=a
					break
				a=a.NextSibling()
				if a == None:
					endof=True
					break
			if endof:
				saytxt="Handling wrong configuration, ignoring, not found"
				alert= BAlert('Ops', saytxt, 'Ok', None,None,InterfaceDefs.B_WIDTH_AS_USUAL,alert_type.B_WARNING_ALERT)
				alerts.append(alert)
				alert.Go()
				return
			#self.cmplvl_value=self.boxview.ChildAt(self.boxview.CountChildren()-4)
			b=self.boxview.ChildAt(0)
			endof=False
			while True:
				if type(b)==BStringView:
					self.cmplvl_value=b
					break
				b=b.NextSibling()
				if b == None:
					endof=True
					break
			if endof:
				saytxt="Handling wrong configuration, ignoring"
				alrt= BAlert('Ops', saytxt, 'Ok', None,None,InterfaceDefs.B_WIDTH_AS_USUAL,alert_type.B_WARNING_ALERT)
				alerts.append(alrt)
				alrt.Go()
				return
			ck=read_config_file()
			if ck[0]:
				confile=ck[1]
				v=str(self.slid.Value())
				ent=BEntry(confile.Path())
				if ent.Exists():
					Config.read(confile.Path())
					cfgfile = open(confile.Path(),'w')
					Config.set('Compression','compression', v)
					Config.write(cfgfile)
					cfgfile.close()
					Config.read(confile.Path())
					self.cmplvl_value.SetText(v)
	def FrameResized(self,x,y):
		self.ResizeTo(600,300)

class HTPBZ2Window(BWindow):
	opf=""
	def __init__(self,cmds,args):
		global timings,experimental#,block_size,cmplvl
		BWindow.__init__(self, BRect(200,170,800,278), "TMZ Compressor/Decompressor", window_type.B_TITLED_WINDOW, B_NOT_RESIZABLE |B_QUIT_ON_WINDOW_CLOSE)
		self.bckgnd = BView(self.Bounds(), "bckgnd_View", 8, 20000000)
		rect=self.bckgnd.Bounds()
		self.AddChild(self.bckgnd,None)
		self.bckgnd.SetResizingMode(B_FOLLOW_ALL_SIDES)
		bckgnd_bounds=self.bckgnd.Bounds()
		self.box = BBox(BRect(0,0,bckgnd_bounds.Width(),bckgnd_bounds.Height()),"Underbox",0x0202|0x0404,border_style.B_FANCY_BORDER)
		self.compelbox = BBox(BRect(0,0,bckgnd_bounds.Width(),bckgnd_bounds.Height()),"Compression_box",0x0202|0x0404,border_style.B_FANCY_BORDER)
		self.extrelbox = BBox(BRect(0,0,bckgnd_bounds.Width(),bckgnd_bounds.Height()),"Extraction_box",0x0202|0x0404,border_style.B_FANCY_BORDER)
		self.bckgnd.AddChild(self.compelbox, None)
		self.bckgnd.AddChild(self.extrelbox, None)
		self.iwheel=0
		self.steps=['˹','   ˺','   ˼','˻']
		self.extrelbox.Hide()
		self.compelbox.Hide()
		self.bckgnd.AddChild(self.box, None)
		fon=BFont()
		fon.SetSize(24)
		txt="Processing..."
		self.cwip=BStringView(BRect(8,8,16+fon.StringWidth(txt),16+fon.Size()),"comp_el",txt)
		self.cwip.SetFont(fon)
		txt2="Creating tar archive..."
		self.cwip2=BStringView(BRect(8,20+fon.Size(),self.compelbox.Bounds().right-8,24+fon.Size()*2),"comp_job",txt2)
		self.cwip2.SetFont(fon)
		self.cantihalt=BStringView(BRect(self.compelbox.Bounds().right-16-fon.StringWidth(self.steps[2]),self.compelbox.Bounds().bottom-8-fon.Size(),self.compelbox.Bounds().right-8,self.compelbox.Bounds().bottom-8),"comp_wheel",self.steps[0])
		self.cantihalt.SetFont(fon)
		self.eantihalt=BStringView(BRect(self.compelbox.Bounds().right-16-fon.StringWidth(self.steps[2]),self.compelbox.Bounds().bottom-8-fon.Size(),self.compelbox.Bounds().right-8,self.compelbox.Bounds().bottom-8),"extr_wheel",self.steps[0])
		self.eantihalt.SetFont(fon)
		self.ewip=BStringView(BRect(8,8,16+fon.StringWidth(txt),16+fon.Size()),"extr_el",txt)
		self.ewip.SetFont(fon)
		txt3="Decompressing BZip2 file..."
		self.ewip2=BStringView(BRect(8,20+fon.Size(),self.extrelbox.Bounds().right-8,24+fon.Size()*2),"extr_job",txt3)
		self.ewip2.SetFont(fon)
		self.compelbox.AddChild(self.cwip,None)
		self.compelbox.AddChild(self.cwip2,None)
		self.compelbox.AddChild(self.cantihalt,None)
		self.extrelbox.AddChild(self.ewip,None)
		self.extrelbox.AddChild(self.ewip2,None)
		self.extrelbox.AddChild(self.eantihalt,None)
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
		self.commutedfp=False
		self.clicked=False
		self.ofp=BFilePanel(B_OPEN_PANEL,None,None,node_flavor.B_ANY_NODE,True, None, None, True, True)
		self.autoload=""
		self.autorun=False
		self.setcmd=False
		experimental=False
		osdir="/boot/home/Desktop"
		osfile="/boot/home/Desktop/output.tmz"
		if args!=[]:
			for f in args:
				f=os.path.abspath(f)
				if self.autoload=="":
					self.autoload+=f
				else:
					self.autoload+=","+f
			self.input.SetText(self.autoload)
		for cmd in cmds:
			if cmd=="c":
				self.commutedfp=False
				self.rb1.SetValue(1)
				self.rb2.SetValue(0)
				self.list_autol=self.autoload.split(',')
				a=self.list_autol[0]
				open_file=os.path.basename(os.path.abspath(a))
				if BEntry(a).Exists():
					osdir=os.path.dirname(os.path.abspath(a))
					if len(self.list_autol)>1:
						osfile=osdir+"/"+os.path.basename(os.path.abspath(osdir))+".tmz"
					else:
						osfile=os.path.abspath(a)+".tmz"
				else:
					osdir=os.getcwd()
					if len(self.list_autol)>1:
						osfile=os.path.basename(os.path.abspath(osdir))+".tmz"
					else:
						osfile=os.path.basename(os.path.abspath(a))+".tmz"
				if os.access(os.path.dirname(osfile), os.W_OK):
					self.output.SetText(osfile)
				else:
					osfile="/boot/home/Desktop/"+os.path.basename(osfile)
					self.output.SetText(osfile)
				self.output.SetText(osfile)
				self.setcmd=True
				if self.autorun and self.autoload!="":
					be_app.WindowAt(0).PostMessage(1024)
			elif cmd=="d":
				self.fp=BFilePanel(B_OPEN_PANEL,None,None,node_flavor.B_DIRECTORY_NODE,False, None, None, True, True)
				self.commutedfp=True
				self.rb1.SetValue(0)
				self.rb2.SetValue(1)
				self.list_autol=self.autoload.split(',')
				open_file=os.path.basename(self.list_autol[0])
				osdir=os.path.dirname(os.path.abspath(self.list_autol[0]))
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
				self.setcmd=True
				if self.autorun and self.autoload!="":
					be_app.WindowAt(0).PostMessage(1024)
			elif cmd=="g":
				if not self.autorun:
					self.autorun=True
					if self.setcmd and self.autoload!="":
						be_app.WindowAt(0).PostMessage(1024)
			elif cmd=="e":
				experimental=True
		
		self.fp.SetPanelDirectory(osdir)
		self.fp.SetSaveText(osfile)
		
		self.ofp.SetPanelDirectory(osdir)
		try:
			self.ofp.SetSaveText(open_file)
		except:
			pass

	def MessageReceived(self, msg):
		global block_size,cmplvl,alerts
		if msg.what == 207:
			self.opf=""
			self.ofp.Show()
		elif msg.what == struct.unpack('!l',b'DATA')[0]:
			self.input.TextView().SelectAll()
			self.input.TextView().Clear()
			i=0
			a=entry_ref()
			while True:
				try:
					msg.FindRef("refs",i,a)
					perc=BPath()
					entr=BEntry(a)
					if entr.Exists():
						entr.GetPath(perc)
						actualtxt=self.input.Text()
						if actualtxt=="":
							self.input.SetText(perc.Path())
						else:
							self.input.SetText(actualtxt+","+perc.Path())
					else:
						break
					i+=1
				except:
					break
		elif msg.what == 54173:
			er=entry_ref()
			self.fp.GetPanelDirectory(er)
			eny=BEntry(er)
			patho=BPath()
			eny.GetPath(patho)
			name = msg.FindString("name")
			self.output.SetText(patho.Path()+"/"+name)
		elif msg.what == 107:
			if timings:
				self.etime=time.time()
				saytxt="Elapsed time: "+str(self.etime-self.stime)
				infoA=BAlert('Ops', saytxt, 'Ok', None,None,InterfaceDefs.B_WIDTH_AS_USUAL,alert_type.B_INFO_ALERT)
				alerts.append(infoA)
				infoA.Go()
			self.GoBtn.SetEnabled(True)
			self.compelbox.Hide()
			self.extrelbox.Hide()
			self.box.Show()
		elif msg.what == 66:
			self.iwheel+=1
			if self.iwheel==4:
				self.iwheel=0
			self.cantihalt.SetText(self.steps[self.iwheel])
			self.eantihalt.SetText(self.steps[self.iwheel])
		elif msg.what == 307:
			self.clicked=True
			self.fp.Show()
		elif msg.what == 407:
			self.settings_window = SettingsWindow()
			self.settings_window.Show()
		elif msg.what == 507:
			self.cwip2.SetText("Parallel BZip2 compression...")
		# elif msg.what == 607:
			# self.ewip2.SetText("Extracting tar archive...")
		# elif msg.what == 707:
			# self.ewip2.SetText("Decompressing BZip2 file...")
		elif msg.what == 807:
			txt=msg.FindString("new_extraction_label")
			self.ewip2.SetText(txt)
		elif msg.what == 714:
			saytxt=msg.FindString("error")
			infoA=BAlert('Ops', saytxt, 'Ok', None,None,InterfaceDefs.B_WIDTH_AS_USUAL,alert_type.B_WARNING_ALERT)
			alerts.append(infoA)
			infoA.Go()
		elif msg.what == 1024:
			if timings:
				self.stime=time.time()
			self.list_autol=self.input.Text().split(",")
			if self.rb1.Value():
				self.GoBtn.SetEnabled(False)
				self.box.Hide()
				self.compelbox.Show()
				self.cwip2.SetText("Creating tar archive...")
				
				fout=self.output.Text()
				if fout=="":
					supposedpath=os.path.abspath(self.list_autol[0])+".tmz"
					if os.access(os.path.dirname(supposedpath), os.W_OK):
						fout=supposedpath
					else:
						fout="/boot/home/Desktop/"+os.path.basename(self.list_autol[0])+".tmz"
				else:
					if not os.access(os.path.dirname(fout), os.W_OK):
						supposedpath="/boot/home/Desktop/"+os.path.basename(fout)+".tmz"
						self.output.SetText(supposedpath)
						fout=supposedpath
				thr=Thread(target=create_compressed_archive,args=(self.list_autol,fout,block_size,cmplvl,self.autorun,cinram,))
				thr.start()
			else:
				paths=self.input.Text().split(",")
				for s in paths:
					if s[-1]=="/":
						s=s[:-1]
				if self.output.Text()=="":
					try:
						supposedpath=os.path.dirname(os.path.abspath(paths[0]))
						if os.access(supposedpath, os.W_OK):
							self.output.SetText(supposedpath)
						else:
							self.output.SetText("/boot/home/Desktop")
					except:
						self.output.SetText("/boot/home/Desktop")
				else:
					supposedpath = self.output.Text()
					if os.access(supposedpath, os.W_OK):
						if supposedpath[-1]=="/":
							self.output.SetText(supposedpath[:-1])
					else:
						self.output.SetText("/boot/home")
				self.GoBtn.SetEnabled(False)
				self.box.Hide()
				self.extrelbox.Show()
				ck=read_config_file()
				if ck[0]:
					confile=ck[1]
					ent=BEntry(confile.Path())
					if ent.Exists():
						Config.read(confile.Path())
						strinram=ConfigSectionMap("Decompression")["inram"]
						if strinram=="True":
							inram=True
						else:
							inram=False
					else:
						inram=False
				else:
					inram=False
				Thread(target=launch_extractions,args=(paths,self.output.Text(),self.autorun,inram)).start()
			self.autorun=False
			self.setcmd=False
		elif msg.what == 191:
			osdir="/boot/home/Desktop"
			osfile="/boot/home/Desktop/output.tmz"
			self.fp=BFilePanel(B_SAVE_PANEL,None,None,0,False, None, None, True, True)
			self.fp.SetPanelDirectory(osdir)
			self.ofp.SetPanelDirectory(osdir)
			self.fp.SetSaveText("output.tmz")
			self.input.TextView().SelectAll()
			self.input.TextView().Clear()
			self.output.TextView().SelectAll()
			self.output.TextView().Clear()
		elif msg.what == 181:
			osdir="/boot/home/Desktop"
			osfile="/boot/home/Desktop"
			self.fp=BFilePanel(B_OPEN_PANEL,None,None,node_flavor.B_DIRECTORY_NODE,False, None, None, True, True)
			self.fp.SetPanelDirectory(osdir)
			self.ofp.SetPanelDirectory(osdir)
			self.input.TextView().SelectAll()
			self.input.TextView().Clear()
			self.output.TextView().SelectAll()
			self.output.TextView().Clear()
		elif msg.what == 45371:
			percors=msg.FindString("path")
			if self.commutedfp and self.clicked:
				self.output.SetText(percors)
				self.clicked=False
			else:
				if self.opf == "":
					self.opf="".join(percors)
				else:
					self.opf=self.opf+","+percors
				self.input.SetText(self.opf)
				self.list_autol=self.opf.split(",")
		elif msg.what == 1800:
			self.list_autol=self.input.Text().split(",")
		return BWindow.MessageReceived(self,msg)
	def QuitRequested(self):
		#wnum = be_app.CountWindows()
		#if wnum>1:
		#	if len(self.tmpWind)>0:
		#		for wind in self.tmpWind:
		#			wind.Lock()
		#			wind.Quit()
		return BWindow.QuitRequested(self)
		
class ReportWindow(BWindow):
	def __init__(self):
		global alerts,reps
		reps=[]
		scr=BScreen()
		scrfrm=scr.Frame()
		x=scrfrm.Width()/2-400
		xf=x+800
		y=scrfrm.Height()/3
		yf=scrfrm.Height()*2/3
		self.deltay=yf-y
		BWindow.__init__(self, BRect(x,y,xf,yf), "Report", window_type.B_FLOATING_WINDOW,  B_NOT_RESIZABLE|B_CLOSE_ON_ESCAPE)
		self.bckgnd = BView(self.Bounds(), "bckgnd_View", 8, 20000000)
		bckgnd_bounds=self.bckgnd.Bounds()
		self.AddChild(self.bckgnd,None)
		self.bckgnd.SetResizingMode(B_FOLLOW_ALL_SIDES)
		self.Reports = ScrollView(BRect(4 , 4, bckgnd_bounds.Width()-22, bckgnd_bounds.Height()-4 ), 'ReportScrollView',True)
		self.bckgnd.AddChild(self.Reports.sv,None)
	def MessageReceived(self, msg):
		global reps
		if msg.what == 53:
			it=self.Reports.lv.ItemAt(self.Reports.lv.CurrentSelection())
			#pth=it.filename
			parent=Path(it.filename).parent
			#print(it.filename,parent)
			subprocess.run(["open", parent])
		elif msg.what == 12345:
			txt=msg.FindString("testo")
			self.Reports.lv.AddItem(BStringItem(txt))
		elif msg.what == 54321:
			fileno=msg.FindString("fileno")
			attrib=msg.FindString("attrib")
			result=msg.FindBool("result")
			reps.append(ReportAttribItem(fileno,attrib,result))
			self.Reports.lv.AddItem(reps[-1])
		elif msg.what == 51423:
			fileno=msg.FindString("fileno")
			result=msg.FindBool("result")
			reps.append(ReportItem(fileno,result))
			self.Reports.lv.AddItem(reps[-1])
		return BWindow.MessageReceived(self,msg)
		
	def FrameResized(self,x,y):
		self.ResizeTo(800,self.deltay)
class ReportItem(BListItem):
	def __init__(self,filename,result):
		self.result=result
		self.filename=filename
		self.fon=BFont()
		self.font_height_value=font_height()
		self.fon.GetHeight(self.font_height_value)
		BListItem.__init__(self)
	def DrawItem(self, owner, frame, complete):
		if self.result:
			owner.SetHighColor(0,255,0,255)
		else:
			owner.SetHighColor(255,0,0,255)
		owner.SetLowColor(0,0,0,0)
		if self.IsSelected() or complete:
			owner.SetHighColor(200,200,200,255)
			owner.SetLowColor(200,200,200,255)
		owner.FillRect(frame)
		owner.SetHighColor(255,255,255,0)
		owner.MovePenTo(frame.left+5,frame.bottom-self.font_height_value.descent)
		owner.DrawString(self.filename,None)
		owner.SetLowColor(255,255,255,255)
class ReportAttribItem(BListItem):
	def __init__(self,filename,attribute,result):
		self.result=result
		self.attribute=attribute
		self.filename=filename
		self.fon=BFont()
		self.font_height_value=font_height()
		self.fon.GetHeight(self.font_height_value)
		BListItem.__init__(self)
	def DrawItem(self, owner, frame, complete):
		owner.SetHighColor(255,255,255,255)
		owner.SetLowColor(0,0,0,0)
		if self.IsSelected() or complete:
			owner.SetHighColor(200,200,200,255)
			owner.SetLowColor(200,200,200,255)
		owner.FillRect(frame)
		if self.result:
			owner.SetHighColor(0,150,0,0)
		else:
			owner.SetHighColor(150,0,0,0)
		owner.MovePenTo(frame.left+5,frame.bottom-self.font_height_value.descent)
		owner.DrawString(self.attribute,None)
		spazio=frame.left+5+self.fon.StringWidth(self.attribute)+5
		owner.MovePenTo(spazio,frame.bottom-self.font_height_value.descent)
		owner.DrawString(self.filename,None)
		owner.SetLowColor(255,255,255,255)
def launch_extractions(paths,outputxt,autoclose,inram=False):
	global alerts
	try:
		for path in paths:
			txt="Decompressing BZip2 file..."
			pmsg=BMessage(807)
			pmsg.AddString("new_extraction_label",txt)
			be_app.WindowAt(0).PostMessage(BMessage(pmsg))#707
			suf="".join(Path(path).suffixes)
			out=os.path.basename(path[:-len(suf)])
			complout=outputxt+"/"+out
			decompress_archive(path, complout,inram=inram)
		if autoclose:
			be_app.WindowAt(0).PostMessage(B_QUIT_REQUESTED)
	except Exception as e:
		txt="Error: "+str(e)
		alert= BAlert('Ops', txt, 'Ok', None,None,InterfaceDefs.B_WIDTH_AS_USUAL,alert_type.B_STOP_ALERT)
		alerts.append(alert)
		alert.Go()
		be_app.WindowAt(0).PostMessage(BMessage(107))

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

def get_type_string(value):
	type_string = struct.pack('>I', value).decode('utf-8')
	return type_string

def compress_block(block, compresslevel):
    return bz2.compress(block, compresslevel=compresslevel)

def parallel_compress_file(input_file, output_file, block_size=1024*1024, compresslevel=9):
	global num_cpus
	file_size = os.path.getsize(input_file)
	# Se il file è più piccolo del block_size, comprimi senza parallellismo
	if file_size < block_size:
		with open(input_file, 'rb') as f:
			data = f.read()
		compressed_data = bz2.compress(data, compresslevel)
		with open(output_file, 'wb') as f:
			f.write(compressed_data)
	else:
		with open(input_file, 'rb') as f:
			blocks = []
			while True:
				block = f.read(block_size)
				if not block:
					break
				blocks.append(block)
		with multiprocessing.Pool(num_cpus) as pool:
			compress_partial = partial(compress_block, compresslevel=compresslevel)
			compressed_blocks = pool.map(compress_partial, blocks)
        
		with open(output_file, 'wb') as f:
			for compressed_block in compressed_blocks:
				f.write(compressed_block)

def parallel_compress_in_ram_file(input_data, output_file, block_size=1024*1024, compresslevel=9):
	global num_cpus
	blocks = []
	while True:
		block = input_data.read(block_size)
		if not block:
			break
		blocks.append(block)

	with multiprocessing.Pool(num_cpus) as pool:
			compress_partial = partial(compress_block, compresslevel=compresslevel)
			compressed_blocks = pool.map(compress_partial, blocks)
        
	with open(output_file, 'wb') as f:
		for compressed_block in compressed_blocks:
			f.write(compressed_block)

def add_attributes_to_tar(tar, path,cutter,md5_file=None):
	global save_hash,endianness
	nf=BNode(path)
	try:
		attributes=attr(nf)
	except Exception as e:
		print("skipping attributes for",path,"\n",e)
		attributes=[]
	if len(attributes)>0:
		attr_data = {}
		for name, (attr_type, attr_size, attr_value) in attributes:
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
							print("ripiego salvato in intero a "+str(numb*8)+"bit")
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
		#print(md5attr_json)#TODO: Check on extract this checksum
		newpath="./"+os.path.relpath(path,cutter)
		attr_info = tarfile.TarInfo(name=f"{newpath}.{md5attr_json}.attr")
		attr_info.size = len(attr_json)
		
			
		#with open("jsondata.txt", 'w') as f:
		#	f.write(attr_json.decode("utf-8"))
		tar.addfile(attr_info, io.BytesIO(attr_json))
		if save_hash and md5_file!=None:
			md5data=md5_file.encode('utf-8')
			chksum_info = tarfile.TarInfo(name=f"{newpath}.TMZchecksum")
			chksum_info.size = len(md5data)
			tar.addfile(chksum_info, io.BytesIO(md5data))

def find_common_root(paths):
    try:
        common_root = os.path.commonpath(paths)
        return common_root
    except ValueError:
        # Handle the case where there is no common path
        return None

###### Note: due to limitations in Haiku, apps memory is limited to something about 2GB of ram
######       then io.Bytes() cannot be used for big files. To operate in ram it has been used the
######       /boot/system/var/shared_memory path that provides a RAM_FS space
#def create_tar_in_ram_with_attributes(input_paths):
#		#tar_data = io.BytesIO()
#		#with tarfile.open(tar_data, mode="w") as tar:
#			tar_data = io.BytesIO()
#			tar=tarfile.open(fileobj=tar_data,mode='w')
#			if len(input_paths)>1:
#				cutter=find_common_root(input_paths)
#			else:
#				cutter=Path(input_paths[0]).parent
#			for input_path in input_paths:
#				if cutter==None:
#					cutter=os.path.dirname(input_path)+"/"
#				relative_path = "./"+os.path.relpath(input_path, cutter)
#				tar.add(input_path, arcname=relative_path)
#				if os.path.isfile(input_path):
#					add_attributes_to_tar(tar, input_path,cutter)
#				elif os.path.isdir(input_path):
#					add_attributes_to_tar(tar,input_path,cutter)
#					for root, _, files in os.walk(input_path):
#						for dir in _:
#							dir_path = os.path.join(root,dir)
#							add_attributes_to_tar(tar,dir_path,cutter)
#						for file in files:
#							file_path = os.path.join(root, file)
#							add_attributes_to_tar(tar, file_path,cutter)
#			#tar_data.seek(0)
#			#return tar_data
#			return tar.read()
def create_tar_with_attributes(input_paths, tar_file):
		with tarfile.open(tar_file, "w") as tar:
			if len(input_paths)>1:
				cutter=find_common_root(input_paths)
			else:
				cutter=Path(input_paths[0]).parent
			for input_path in input_paths:
				if cutter==None:
					cutter=os.path.dirname(input_path)+"/"
				relative_path = "./"+os.path.relpath(input_path, cutter)
				if save_hash and os.path.isfile(input_path):
					with open(input_path, 'rb') as f:
						data = f.read()
						md5_returned = get_bytes_md5(data)
				else:
					md5_returned=None
				tar.add(input_path, arcname=relative_path)
				if os.path.isfile(input_path):
					add_attributes_to_tar(tar, input_path,cutter,md5_returned)
				elif os.path.isdir(input_path):
					add_attributes_to_tar(tar,input_path,cutter)
					for root, _, files in os.walk(input_path):
						for dir in _:
							dir_path = os.path.join(root,dir)
							add_attributes_to_tar(tar,dir_path,cutter)
						for file in files:
							file_path = os.path.join(root, file)
							if save_hash:
								with open(file_path, 'rb') as f:
									data = f.read()
									md5_returned = get_bytes_md5(data)
							else:
								md5_returned=None
							add_attributes_to_tar(tar, file_path,cutter,md5_returned)

def create_tarbz2_with_attributes(input_paths, out_file,compresslevel=9):
		global save_hash
		with tarfile.open(out_file, "w:bz2") as tar:
			if len(input_paths)>1:
				cutter=find_common_root(input_paths)
			else:
				cutter=Path(input_paths[0]).parent
			for input_path in input_paths:
				if cutter==None:
					cutter=os.path.dirname(input_path)+"/"
				relative_path = "./"+os.path.relpath(input_path, cutter)
				if save_hash and os.path.isfile(input_path):
					with open(input_path, 'rb') as f:
						data = f.read()
						md5_returned = get_bytes_md5(data)
				else:
					md5_returned=None
				tar.add(input_path, arcname=relative_path)
				if os.path.isfile(input_path):
					add_attributes_to_tar(tar, input_path,cutter,md5_returned)
				elif os.path.isdir(input_path):
					add_attributes_to_tar(tar,input_path,cutter)
					for root, _, files in os.walk(input_path):
						for dir in _:
							dir_path = os.path.join(root,dir)
							add_attributes_to_tar(tar,dir_path,cutter)
						for file in files:
							file_path = os.path.join(root, file)
							if save_hash:
								with open(file_path, 'rb') as f:
									data = f.read()
									md5_returned = get_bytes_md5(data)
							else:
								md5_returned=None
							add_attributes_to_tar(tar, file_path,cutter,md5_returned)

def create_compressed_archive(input_paths, output_file, block_size=1024*1024, compresslevel=9,autoclose=False,cinram=False):
	global alerts,cparallelization
	try:
		if os.path.isdir(output_file): #compensate luser that indicates a directory
			if output_file[-1]=="/":
				output_file=output_file[:-1]
				output_file=os.path.join(output_file,output_file.split("/")[-1])
		if cparallelization==0:
			if cinram:
				tar_file = "/boot/system/var/shared_memory/tar_file.tar"
			else:
				tar_file = output_file + '.tar'
			create_tar_with_attributes(input_paths, tar_file)
			be_app.WindowAt(0).PostMessage(BMessage(507))
			parallel_compress_file(tar_file, output_file, block_size, compresslevel)
			os.remove(tar_file)
		else:
			create_tarbz2_with_attributes(input_paths,output_file,compresslevel)
		
		be_app.WindowAt(0).PostMessage(BMessage(107))
		#if not cinram:
		#	tar_file = output_file + '.tar'
		#	create_tar_with_attributes(input_paths, tar_file)
		#	be_app.WindowAt(0).PostMessage(BMessage(507))
		#	parallel_compress_file(tar_file, output_file, block_size, compresslevel)
		#	os.remove(tar_file)
		#	be_app.WindowAt(0).PostMessage(BMessage(107))
		#else:
		#	tar_data=create_tar_in_ram_with_attributes(input_paths)
		#	be_app.WindowAt(0).PostMessage(BMessage(507))
		#	parallel_compress_in_ram_file(tar_data, output_file, block_size, compresslevel)
		#	be_app.WindowAt(0).PostMessage(BMessage(107))
		if autoclose:
			be_app.WindowAt(0).PostMessage(B_QUIT_REQUESTED)
	except Exception as e:
		txt="Error: "+str(e)
		alert= BAlert('Ops', txt, 'Ok', None,None,InterfaceDefs.B_WIDTH_AS_USUAL,alert_type.B_STOP_ALERT)
		alerts.append(alert)
		alert.Go()
		be_app.WindowAt(0).PostMessage(BMessage(107))

def decompress_bz2(input_file):
    with bz2.BZ2File(input_file, 'rb') as file:
        return file.read()

	
def decompress__bz2_in_file(input_file, output_file, block_size=1024*1024):
	with bz2.BZ2File(input_file, 'rb') as f_in, open(output_file, 'wb') as f_out:
		while True:
			block = f_in.read(block_size)
			if not block:
				break
			f_out.write(block)

def ensure_dir_exists(directory):
	if not os.path.exists(directory):
		try:
			os.makedirs(directory)
		except:
			pass

def extract_member_reworked(tar_data, member, output_dir, inram):
	#try:
		member_path = os.path.join(output_dir, member.name[2:])
		# Ensure the directory exists
		if member.isdir():
			ensure_dir_exists(member_path)
		else:
			parent_dir = os.path.dirname(member_path)
			ensure_dir_exists(parent_dir)
		tar_data.extract(member, output_dir)
	#except Exception as exc:
	#	print(f"Generated an exception: {exc}")

def extract_and_set_attributes_batch_reworked(member_batch, tar_data, output_dir, inram):
	tar_data=tarfile.open(tar_data, "r")
	for member in member_batch:
		#try:
			#print(member)
			extract_member_reworked(tar_data, member, output_dir, inram)
			if member.name.endswith('.attr'):
				attr_path = os.path.join(output_dir, member.name)
				original_file = attr_path[:-38]  # Rimuove sia .attr che .{hash}
				with open(attr_path, 'r') as f:
					attr_data = json.load(f)
					set_attributes(original_file, attr_data)
				os.remove(attr_path)
		#except Exception as exc:
		#	print("Eccezione:",exc)

def set_attributes(file_path, attr_data):
	global check_hash, endianness,alerts

	for name, details in attr_data.items():
		attr_value = details['value']
		attr_type = details['type']
		attr_size = details['size']
		# if check_hash:
		try:
			attr_hash = details['hash']
		except:
			if check_hash:
				txt=(f"Checksum checks disabled: missing checksum hashes in attribs data")
				almsg=BMessage(714)
				almsg.AddString("error",txt)
				be_app.WindowAt(0).PostMessage(almsg)
				almsg=BMessage(12345)
				txt="missing checksum hashes in attribs data"
				almsg.AddString("testo",txt)
				be_app.WindowAt(0).PostMessage(almsg)
				for w in alerts:
					if type(w)==ReportWindow:
						w.PostMessage(almsg)
			check_hash = False
		if check_hash:
			almsg=BMessage(54321)
			almsg.AddString("fileno",file_path)
			almsg.AddString("attrib",name)
		node = BNode(file_path)
		ck = get_type_string(details['type'])
		if ck == 'RAWT':
			attr_value = base64.b64decode(attr_value)
			if check_hash:
				if get_bytes_md5(attr_value) == attr_hash:
					almsg.AddBool("result",True)
					#print(file_path, name, "attribute checksum OK")
				else:
					almsg.AddBool("result",False)
					#print(file_path, name, "attribute checksum Failed")
		elif ck == 'LONG':
			attr_value = int(attr_value)
			attr_value = attr_value.to_bytes(4, byteorder=endianness)
			if check_hash:
				if get_bytes_md5(attr_value) == attr_hash:
					almsg.AddBool("result",True)
					#print(file_path, name, "attribute checksum OK")
				else:
					almsg.AddBool("result",False)
					#print(file_path, name, "attribute checksum Failed")
		elif ck == 'LLNG':
			attr_value = int(attr_value)
			attr_value = attr_value.to_bytes(8, byteorder=endianness)
			if check_hash:
				if get_bytes_md5(attr_value) == attr_hash:
					almsg.AddBool("result",True)
					#print(file_path, name, "attribute checksum OK")
				else:
					almsg.AddBool("result",False)
					#print(file_path, name, "attribute checksum Failed")
		elif ck == 'TIME':
			if check_hash:
				if get_bytes_md5(int(attr_value).to_bytes(8, byteorder=endianness)) == attr_hash:
					almsg.AddBool("result",True)
					#print(file_path, name, "attribute checksum OK")
				else:
					almsg.AddBool("result",False)
					#print(file_path, name, "attribute checksum Failed")
			attr_value = int(attr_value).to_bytes(8, byteorder=endianness)
		elif ck == 'CSTR' or ck == 'MIMS':
			attr_value = str.encode(attr_value)
			if check_hash:
				if get_bytes_md5(attr_value) == attr_hash:
					almsg.AddBool("result",True)
					#print(file_path, name, "attribute checksum OK")
				else:
					almsg.AddBool("result",False)
					#print(file_path, name, "attribute checksum Failed")
		elif ck == 'BOOL':
			attr_value = bytes(attr_value, 'utf-8')
			if check_hash:
				if get_bytes_md5(attr_value) == attr_hash:
					almsg.AddBool("result",True)
					#print(file_path, name, "attribute checksum OK")
				else:
					almsg.AddBool("result",False)
					#print(file_path, name, "attribute checksum Failed")
		elif ck == 'FLOT':
			attr_value = base64.b64decode(attr_value)
			if check_hash:
				if get_bytes_md5(attr_value) == attr_hash:
					almsg.AddBool("result",True)
					#print(file_path, name, "attribute checksum OK")
				else:
					almsg.AddBool("result",False)
					#print(file_path, name, "attribute checksum Failed")
		elif ck == 'DBLE':
			attr_value = base64.b64decode(attr_value)
			if check_hash:
				if get_bytes_md5(attr_value) == attr_hash:
					almsg.AddBool("result",True)
					#print(file_path, name, "attribute checksum OK")
				else:
					almsg.AddBool("result",False)
					#print(file_path, name, "attribute checksum Failed")
		else:
			attr_value = base64.b64decode(attr_value)
			if check_hash:
				if get_bytes_md5(attr_value) == attr_hash:
					almsg.AddBool("result",True)
					#print(file_path, name, "attribute checksum OK")
				else:
					almsg.AddBool("result",False)
					#print(file_path, name, "attribute checksum Failed")
		if check_hash:
			for w in alerts:
				if type(w)==ReportWindow:
					w.PostMessage(almsg)
		node.WriteAttr(name, attr_type, 0, attr_value)


def decompress_archive(input_file, output_dir, block_size=1024*1024, inram=False,num_workers=None):
	global parallelization,check_hash,alerts
	if check_hash:
		reports_window = ReportWindow()
		alerts.append(reports_window)
		reports_window.Show()
	if parallelization!=2:
		if inram:
			tar_file = "/boot/system/var/shared_memory/"+os.path.basename(input_file) + '.tar'
		else:
			tar_file = input_file + '.tar'
		decompress__bz2_in_file(input_file, tar_file, block_size)
		txt="Extracting tar archive..."
		pmsg=BMessage(807)
		pmsg.AddString("new_extraction_label",txt)
		be_app.WindowAt(0).PostMessage(BMessage(pmsg))#607
		tar_data = tarfile.open(tar_file, mode='r')		
		################ memo: Haiku app memory limitations ~2GB
		#tar_data = decompress_bz2(input_file)
		#be_app.WindowAt(0).PostMessage(BMessage(607))
		#tar_data = tarfile.open(fileobj=io.BytesIO(tar_data), mode="r")
		################
		#tar_data = tarfile.open(fileobj=decompress_bz2(input_file), mode="r") Test not working

	if num_workers==None:
		num_cpus = multiprocessing.cpu_count()
	else:
		num_cpus = num_workers
	if parallelization == 0:
		tar_data.extractall(path=output_dir)
######### Attempt to extract tarfile members in a parallel mode, this gives more problems than 
######### achievements due to tar not being thread safe
#		with concurrent.futures.ThreadPoolExecutor(num_cpus) as executor:
#			futures = [executor.submit(extract_member_reworked, tar_data, member, output_dir,inram) for member in tar_data.getmembers()]
#			for future in concurrent.futures.as_completed(futures):
#					#try:
#						future.result()
#					#except Exception as exc:
#					#	print(f"Generated an exception: {exc}")
		txt="Writing attributes..."
		pmsg=BMessage(807)
		pmsg.AddString("new_extraction_label",txt)
		be_app.WindowAt(0).PostMessage(BMessage(pmsg))
		with concurrent.futures.ThreadPoolExecutor(num_cpus) as executor:
			futures = []
			for root, _, files in os.walk(output_dir):
				for file in files:
					if file[-5:]==".attr":
						attr_path = os.path.join(root, file)
						futures.append(executor.submit(process_file, attr_path))
					elif file[-12:]==".TMZchecksum":
						checksum_path = os.path.join(root, file)
						futures.append(executor.submit(check_file, checksum_path))
			for future in concurrent.futures.as_completed(futures):
				try:
					future.result()  # Verifica eventuali eccezioni
				except Exception as e:
					print(f"Errore nell'elaborazione: {e}")
####################################################
## batched parallelization: experimental - differences in output size - todo: check diffs ###
	elif parallelization==1:
		members = tar_data.getmembers()
		member_batch=[]
		batch_size = max(1,len(members) // num_cpus)
		for i in range(0, len(members), batch_size):
			batch = members[i:i + batch_size]
			member_batch.append(batch)
		with concurrent.futures.ThreadPoolExecutor(num_cpus) as executor:
			futures = [executor.submit(extract_and_set_attributes_batch_reworked, batch, tar_file, output_dir,inram) for batch in member_batch]
			for future in concurrent.futures.as_completed(futures):
				#try:
					future.result()
				#except Exception as exc:
				#	print(f"Generated an exception: {exc}")
############ Estrazione lasciata a tar (r:bz2) *******************
	elif parallelization==2:
		txt="Extracting tar.bz2 archive..."
		pmsg=BMessage(807)
		pmsg.AddString("new_extraction_label",txt)
		be_app.WindowAt(0).PostMessage(BMessage(pmsg))
		tar_data = tarfile.open(input_file, mode='r:bz2')
		tar_data.extractall(path=output_dir)
		for member in tar_data.getmembers():
			if member.name.endswith('.attr'):
				try:
					attr_path = os.path.join(output_dir, member.name)
					original_file = attr_path[:-38]  # Rimuove sia .attr che .{hash}
					with open(attr_path, 'r') as f:
						attr_data = json.load(f)
						set_attributes(original_file, attr_data)
				except Exception as exc:
					txt=(f"Errore nel gestire gli attributi di {original_file}: {exc}")
					almsg=BMessage(714)
					almsg.AddString("error",txt)
					be_app.WindowAt(0).PostMessage(almsg)
				os.remove(attr_path)
			if member.name.endswith('.TMZchecksum'):
				try:
					if check_hash:
						checksum_path = os.path.join(output_dir, member.name)
						original_file = checksum_path[:-12]
						with open(checksum_path, 'r') as f:
							svdchksum=f.read()
						with open(original_file, 'rb') as f:
							data=f.read()
							actchksum=get_bytes_md5(data)
						almsg=BMessage(51423)
						almsg.AddString("fileno",original_file)
						if actchksum==svdchksum:
							almsg.AddBool("result",True)
						else:
							almsg.AddBool("result",False)
				except Exception as exc:
					txt=(f"Errore nel gestire i checksum: {exc}")
					almsg=BMessage(714)
					almsg.AddString("error",txt)
					be_app.WindowAt(0).PostMessage(almsg)
				os.remove(checksum_path)
				if check_hash:
					for w in alerts:
						if type(w)==ReportWindow:
							w.PostMessage(almsg)
######## Secuential extraction and assignement of extra attributes ########
	elif parallelization==3:
	### serial - single thread: experimental - differences in output size - todo: check diffs ###
#		with tarfile.open(tar_file, "r") as tar:
#			for member in tar.getmembers():
			for member in tar_data.getmembers():
				try:
					member_path = os.path.join(output_dir, member.name)
					if not os.path.abspath(member_path).startswith(os.path.abspath(output_dir)):
						raise Exception("Tentativo di estrazione fuori dalla directory di destinazione: {}".format(member.name))
					tar_data.extract(member, output_dir)
					if member.name.endswith('.attr'):
						try:
							attr_path = os.path.join(output_dir, member.name)
							original_file = attr_path[:-38]  # Rimuove sia .attr che .{hash}
							with open(attr_path, 'r') as f:
								attr_data = json.load(f)
								set_attributes(original_file, attr_data)
						except Exception as exc:
							txt=(f"Errore nel gestire gli attributi: {exc}")
							almsg=BMessage(714)
							almsg.AddString("error",txt)
							be_app.WindowAt(0).PostMessage(almsg)
						os.remove(attr_path)
				except Exception as e:
					txt=(f"Errore durante l'estrazione del file {member.name}: {e}")
					almsg=BMessage(714)
					almsg.AddString("error",txt)
					be_app.WindowAt(0).PostMessage(almsg)
					break
	#if not inram: #both in ram and on disk are written to a file (shared memory or file-on-disk)
	if parallelization!=2:
		os.remove(tar_file)
	be_app.WindowAt(0).PostMessage(BMessage(107))

def process_file(attr_path):
	original_file = attr_path[:-38]
	ent=BEntry(original_file)
	if ent.Exists():
		with open(attr_path, 'r') as f:
			attr_data = json.load(f)
			set_attributes(original_file, attr_data)
		os.remove(attr_path)
		
def check_file(checksum_path):
	global check_hash
	original_file = checksum_path[:-12]
	ent=BEntry(original_file)
	if ent.Exists():
		if check_hash:
			with open(checksum_path, 'r') as f:
				svdchksum=f.read()
			with open(original_file, 'rb') as f:
				data=f.read()
				actchksum=get_bytes_md5(data)
			almsg=BMessage(51423)
			almsg.AddString("fileno",original_file)
			if actchksum==svdchksum:
				almsg.AddBool("result",True)
			else:
				almsg.AddBool("result",False)
			for w in alerts:
				if type(w)==ReportWindow:
					w.PostMessage(almsg)
		os.remove(checksum_path)

class App(BApplication):
	def __init__(self):
		BApplication.__init__(self, "application/x-python-HTMZ")
		self.realargs=[]
		self.cmd=[]
		self.SetPulseRate(1000000)
	def ReadyToRun(self):
		self.window = HTPBZ2Window(self.cmd,self.realargs)
		self.window.Show()
	def ArgvReceived(self,num,args):# argvReceived is executed before readytorun
		global timings
		#with open("tmp.txt","w") as f:
		#	f.write(str(args))
		timings=False
		realargs=args
		if args[1][-7:]=="HTMZ.py":
			realargs.pop(1)
			realargs.pop(0)
			if len(realargs)>1:
				remit=[]
				for ra in realargs:
					if len(ra)==2 and ra[0]=="-":
						if ra[1] in ["c","d","g","e"]:
							self.cmd.append(ra[1])
							remit.append(ra)
						if ra[1] == "t":
							timings=True
							remit.append(ra)
				for remi in remit:
					realargs.remove(remi)
				self.realargs=realargs
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
		BApplication.MessageReceived(self,msg)

	def Pulse(self):
		be_app.WindowAt(0).PostMessage(BMessage(66))

def write_def_system_config():
	global num_cpus,endianness
	cfgfile = open(confile.Path(),'w')
	Config.add_section('System')
	get_endianness()
	num_cpus=multiprocessing.cpu_count()
	Config.set('System','endianness', endianness)
	Config.set('System','cpus', str(num_cpus))
	Config.write(cfgfile)
	cfgfile.close()

def write_def_compression_config():
	global save_hash,cinram,cmplvl,block_size,cparallelization
	cfgfile = open(confile.Path(),'w')
	Config.add_section('Compression')
	Config.set('Compression','savesum', "False")
	Config.set('Compression','compression', "9")
	Config.set('Compression','block_size', "1048576")
	Config.set('Compression','cinram', "True")
	Config.set('Compression','cparallelization', "0")
	save_hash=False
	cinram=True
	cmplvl=9
	block_size=1048576
	Config.write(cfgfile)
	cfgfile.close()

def write_def_decompression_config():
	cfgfile = open(confile.Path(),'w')
	Config.add_section('Decompression')
	Config.set('Decompression','checksum', "False")
	Config.set('Decompression','parallelization', "0")
	Config.set('Decompression','inram', "True")
	check_hash=False
	parallelization=0
	inram=True
	Config.write(cfgfile)
	cfgfile.close()

def main():
    global be_app
    be_app = App()
    be_app.Run()
	
if __name__ == "__main__":
	global save_hash,check_hash,endianness,parallelization,cmplvl,block_size,num_cpus,inram,cinram,alerts,cparallelization
	alerts=[]
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
		try:
			l=Config["System"]
			if "endianness" in l:
				endianness = ConfigSectionMap("System")["endianness"]
			else:
				cfgfile = open(confile.Path(),'w')
				get_endianness()
				Config.set('System','endianness', endianness)
				Config.write(cfgfile)
				cfgfile.close()
			if "cpus" in l:
				num_cpus = int(ConfigSectionMap("System")["cpus"])
			else:
				cfgfile = open(confile.Path(),'w')
				num_cpus=multiprocessing.cpu_count()
				Config.set('System','cpus', str(num_cpus))
				Config.write(cfgfile)
				cfgfile.close()
		except Exception as e:
			write_def_system_config()
		Config.read(confile.Path())
		try:
			l=Config["Compression"]
			if "savesum" in l:
				value = ConfigSectionMap("Compression")["savesum"]
				if value == "True":
					save_hash=True
				else:
					save_hash=False
			else:
				cfgfile = open(confile.Path(),'w')
				save_hash=False
				Config.set('Compression','savesum', "False")
				Config.write(cfgfile)
				cfgfile.close()
			if "compression" in l:
				cmplvl = int(ConfigSectionMap("Compression")["compression"])
			else:
				cfgfile = open(confile.Path(),'w')
				Config.set('Compression','compression', "9")
				cmplvl=9
				Config.write(cfgfile)
				cfgfile.close()
			if "block_size" in l:
				block_size = int(ConfigSectionMap("Compression")["block_size"])
			else:
				cfgfile = open(confile.Path(),'w')
				Config.set('Compression','block_size', "1048576")
				block_size=1048576
				Config.write(cfgfile)
				cfgfile.close()
			if "cinram" in l:
				value = ConfigSectionMap("Compression")["cinram"]
				if value == "True":
					cinram=True
				else:
					cinram=False
			else:
				cfgfile = open(confile.Path(),'w')
				Config.set('Compression','cinram', "True")
				cinram=True
				Config.write(cfgfile)
				cfgfile.close()
			if 	"cparallelization" in l:
				cparallelization = int(ConfigSectionMap("Compression")["cparallelization"])
			else:
				cfgfile = open(confile.Path(),'w')
				Config.set('Compression','cparallelization', "0")
				cparallelization=0
				Config.write(cfgfile)
				cfgfile.close()
		except Exception as e:
			write_def_compression_config()
		Config.read(confile.Path())
		try:
			l = Config["Decompression"]
			if "checksum" in l:
				value = ConfigSectionMap("Decompression")["checksum"]
				if value == "True":
					check_hash=True
				else:
					check_hash=False
			else:
				cfgfile = open(confile.Path(),'w')
				Config.set('Decompression','checksum', "False")
				check_hash=False
				Config.write(cfgfile)
				cfgfile.close()
			if "parallelization" in l:
				parallelization = int(ConfigSectionMap("Decompression")["parallelization"])
			else:
				cfgfile = open(confile.Path(),'w')
				Config.set('Decompression','parallelization', "0")
				parallelization=0
				Config.write(cfgfile)
				cfgfile.close()
			if "inram" in l:
				value = ConfigSectionMap("Decompression")["inram"]
				if value == "True":
					inram=True
				else:
					inram=False
			else:
				cfgfile = open(confile.Path(),'w')
				Config.set('Decompression','inram', "True")
				inram=True
				Config.write(cfgfile)
				cfgfile.close()
		except Exception as e:
			write_def_decompression_config()
		Config.read(confile.Path())
	else:
		cfgfile = open(confile.Path(),'w')
		Config.add_section('System')
		get_endianness()
		num_cpus=multiprocessing.cpu_count()
		Config.set('System','endianness', endianness)
		Config.set('System','cpus', str(num_cpus))
		Config.add_section('Compression')
		Config.set('Compression','savesum', "False")
		Config.set('Compression','compression', "9")
		Config.set('Compression','block_size', "1048576")
		Config.set('Compression','cinram', "True")
		Config.set('Compression','cparallelization', "0")
		Config.add_section('Decompression')
		Config.set('Decompression','checksum', "False")
		Config.set('Decompression','parallelization', "0")
		Config.set('Decompression','inram', "True")
		cinram=True
		check_hash=False
		parallelization=0
		cparallelization=0
		save_hash=False
		inram=True
		cmplvl=9
		block_size=1048576
		Config.write(cfgfile)
		cfgfile.close()
		Config.read(confile.Path())

	main()
