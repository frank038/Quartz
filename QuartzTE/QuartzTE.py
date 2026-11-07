#!/usr/bin/env python3

VERSION = "0.8.0 beta"
ENAME = "Quartz"
ESITE = "https://github.com/frank038/Quartz"

import sys,os,shutil
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Vte', '3.91')
gi.require_version('Pango', '1.0')
from gi.repository import Gtk,Gdk,GLib,Gio,Vte,Pango,GObject
import json
import subprocess
import signal

self_main = None
_curr_dir = os.getcwd()
_HOME = os.path.expanduser("~")
icon_theme = Gtk.IconTheme.get_for_display(Gdk.Display.get_default())
COMMANDLINE_CWD = None
COMMANDLINE_PWD = None
COMMANDLINE_PEXEC = None

# the directory settings and options
if not os.access(_curr_dir, os.W_OK):
    HOME_CONFIG = os.path.join(_HOME,".config","QuartzTE4")
    try:
        if not os.path.exists(HOME_CONFIG):
            os.mkdir(HOME_CONFIG, mode=0o770)
    except:
        HOME_CONFIG = _curr_dir
    if HOME_CONFIG != _curr_dir:
        try:
            shutil.copytree("/usr/share/QuartzTE/configs", os.path.join(HOME_CONFIG, "configs"))
            shutil.copytree("/usr/share/QuartzTE/icons", os.path.join(HOME_CONFIG, "icons"))
            shutil.copytree("/usr/share/QuartzTE/langs", os.path.join(HOME_CONFIG, "langs"))
        except Exception as E:
            HOME_CONFIG = _curr_dir
else:
    HOME_CONFIG = _curr_dir

sys.path.append(os.path.join(HOME_CONFIG, "langs"))
_lang = __import__("en")

# the clipboard
clipboard = Gdk.Display.get_default().get_clipboard()

config_file = os.path.join(HOME_CONFIG, "configs/config.json")
config_conf_start = { 
"wwidth": 1200, 
"wheight": 800,
"font-size": 10,
"font-family": "monospace",
"foreground-color": "#ffffff"
}
if not os.path.exists(config_file):
    try:
        _data_json = config_conf_start
        _ff =  open(config_file, "w")
        json.dump(_data_json, _ff, indent = 4)
        _ff.close()
        config_conf = config_conf_start
    except:
        sys.exit()
else:
    try:
        _ff = open(config_file, "r")
        config_conf = json.load(_ff)
        _ff.close()
    except:
        sys.exit()

######### CONFIGURATION
WWIDTH = config_conf["wwidth"] # this program width
WHEIGHT = config_conf["wheight"] # this program height
FONT_SIZE = config_conf["font-size"] # font size
FONT_FAMILY = config_conf["font-family"] # font family
FOREGROUND_COLOR = config_conf["foreground-color"] # foreground colour
#########

MENU_XML="""
<?xml version="1.0" encoding="UTF-8"?>
<interface>
  <menu id="app-menu">
    <section>
      <item>
        <attribute name="action">win.new</attribute>
        <attribute name="label" translatable="yes">{}</attribute>
      </item>
      <item>
        <attribute name="action">win.settings</attribute>
        <attribute name="label" translatable="yes">{}</attribute>
      </item>
      <item>
        <attribute name="action">win.about</attribute>
        <attribute name="label" translatable="yes">{}</attribute>
      </item>
      <item>
        <attribute name="action">win.quit</attribute>
        <attribute name="label" translatable="yes">{}</attribute>
    </item>
    </section>
  </menu>
</interface>
""".format(_lang.NEWTERM, _lang.FSETTINGS, _lang.ABOUT, _lang.QUIT)


class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, _files, n_files, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_default_size(WWIDTH, WHEIGHT)
        self.app_ = self.get_application()
        self._files = _files
        self.set_title(ENAME)
        global self_main
        self_main = self
        #
        self.headerbar = Gtk.HeaderBar.new()
        self.headerbar.set_show_title_buttons(True)
        self.set_titlebar(self.headerbar)
        # left headerbar box
        self.lhbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.headerbar.pack_start(self.lhbox)
        # right headerbar box
        self.rhbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.headerbar.pack_end(self.rhbox)
        # hamburger menu
        self.ham_menu = Gtk.MenuButton.new()
        if icon_theme.has_icon("open-menu-symbolic"):
            self.ham_menu.set_icon_name("open-menu-symbolic")
        elif icon_theme.has_icon("application-menu"):
            self.ham_menu.set_icon_name("application-menu")
        if COMMANDLINE_PEXEC == None:
            self.rhbox.append(self.ham_menu)
        # popover menu
        self.ham_pop = Gtk.Popover.new()
        self.ham_pop.set_has_arrow(False)
        self.ham_pop.set_halign(Gtk.Align.START)
        self.ham_menu.set_popover(self.ham_pop)
        ## menu - actions
        quit_action = Gio.SimpleAction.new("quit", None)
        quit_action.connect("activate", self.on_quit_action_actived)
        self.add_action(quit_action)
        #
        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", self.on_about_action_actived)
        self.add_action(about_action)
        #
        settings_action = Gio.SimpleAction.new("settings", None)
        settings_action.connect("activate", self.on_settings_action)
        self.add_action(settings_action)
        #
        new_action = Gio.SimpleAction.new("new", None)
        new_action.connect("activate", self.on_new_action)
        self.add_action(new_action)
        #
        menu = Gtk.Builder.new_from_string(MENU_XML, -1).get_object("app-menu")
        self.ham_menu.set_menu_model(menu)
        #
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_child(self.main_box)
        #
        self.editor_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.main_box.append(self.editor_box)
        #
        self._notebook = Gtk.Notebook.new()
        self.editor_box.append(self._notebook)
        self._notebook.set_focusable(False)
        #
        if self._files and os.path.exists(self._files[0].get_path()):
            _p = self._files[0].get_path()
        else:
            _p = _HOME
        #
        self.new_tab(_p)
        #
        # self._notebook.connect("switch-page", self.on_notebook_switch_page)
        self._notebook.connect("change-current-page", self.on_notebook_change_page)
        self._notebook.connect("page-reordered", self.on_notebook_page_reordered)
        #
        self.connect("close-request", self.on_this_close)
        try:
            self.connect("force-close", self.on_this_close)
        except:
            pass
        self.connect("destroy", self.on_this_close)
        # self.connect("show", self.on_this_show)
    
    # def on_this_show(self, _w):
        # pass
    
    def new_tab(self, _path):
        sw = ScrolWin(self, _path)
        idx = self._notebook.append_page(sw, sw.tab_label)
        self._notebook.set_tab_reorderable(sw, True)
        self._notebook.set_current_page(idx)
        sw.terminal.grab_focus()
        
    def on_new_action(self, action, param):
        self.new_tab(_HOME)
        
    def on_notebook_switch_page(self, _notebook, _sw, i_sw):
        pass
        
    def on_notebook_change_page(self, _notebook, i_sw):
        _sw = _notebook.get_nth_page(i_sw)
    
    def on_notebook_page_reordered(self, notebook, child, page_num):
        child.terminal.grab_focus()
    
    def dialog_action(self, _obj, _res, _data=None):
        _result = _obj.choose_finish(_res)
        if _result == 0:
            if SINGLE_APP == 0:
                self.app_.quit()
            else:
                self.destroy()
        else:
            return
        
    def find_last_process_child(self, _pid):
        ps_command = subprocess.Popen("ps -o pid --ppid {} --noheaders".format(_pid), shell=True, stdout=subprocess.PIPE)
        ps_output = ps_command.stdout.read().decode().strip()
        retcode = ps_command.wait()
        if ps_output == '':
            return _pid
        else:
            _npid = int(ps_output)
            while ps_output != '':
                ps_command = subprocess.Popen("ps -o pid --ppid %d --noheaders" % _npid, shell=True, stdout=subprocess.PIPE)
                ps_output = ps_command.stdout.read().decode().strip()
                retcode = ps_command.wait()
                if ps_output == '':
                    return int(_npid)
                else:
                    _npid = int(ps_output)
        
    def terminate_process(self, _pid):
        ps_command = subprocess.Popen("ps -o pid --ppid {} --noheaders".format(int(_pid)), shell=True, stdout=subprocess.PIPE)
        ps_output = ps_command.stdout.read().decode().strip()
        retcode = ps_command.wait()
        if retcode == 0 and ps_output != '':
            ret = self.find_last_process_child(int(ps_output))
            try:
                os.kill(int(ret), signal.SIGTERM)
                # check
                ps_command = subprocess.Popen("ps -o pid --ppid {} --noheaders".format(_pid), shell=True, stdout=subprocess.PIPE)
                ps_output = ps_command.stdout.read().decode().strip()
                retcode = ps_command.wait()
                if ps_output != '':
                    return -1
                else:
                    self.terminate_process(_pid)
            except:
                return -1
        return 0
    
    def on_quit_action_actived(self, action=None, param=None):
        n_pages = self._notebook.get_n_pages()
        if n_pages > 1:
            for i in range(n_pages):
                _page = self._notebook.get_nth_page(i)
                _terminal = _page.terminal
                ret = self.terminate_process(int(_terminal.pid))
                if ret == -1:
                    return
        #
        self.app_.quit()
    
    def on_this_close(self, _w):
        _term = self._notebook.get_nth_page(0).terminal
        #
        global WWIDTH
        global WHEIGHT
        _WWIDTH = self.get_width()
        _WHEIGHT = self.get_height()
        if _WWIDTH != WWIDTH or _WHEIGHT != WHEIGHT:
            WWIDTH = _WWIDTH
            config_conf["wwidth"] = WWIDTH
            WHEIGHT = _WHEIGHT
            config_conf["wheight"] = WHEIGHT
            try:
                _ff =  open(os.path.join(HOME_CONFIG,"configs/config.json"), "w")
                json.dump(config_conf, _ff, indent = 4)
                _ff.close()
            except:
                pass
        self.on_quit_action_actived(None)
        return True
        
    def on_settings_action(self, action, param=None):
        WinSettings(self)
        
    def on_about_action_actived(self, action, param=None):
        _aboutdial = Gtk.AboutDialog.new()
        _img = Gtk.Image.new_from_file(os.path.join(HOME_CONFIG,"icons","com.quartz.terminal.emulator.svg"))
        _paintable = _img.get_paintable()
        _aboutdial.set_logo(_paintable)
        _aboutdial.set_program_name(ENAME)
        _aboutdial.set_version(VERSION)
        _aboutdial.set_authors(["Philip J. Fry"])
        _aboutdial.set_comments("Made for me 🙂")
        _aboutdial.set_website(ESITE)
        _aboutdial.set_license_type(Gtk.License.GPL_3_0_ONLY)
        _aboutdial.set_transient_for(self_main)
        _aboutdial.present()
        
    def get_font_scaling(self):
        text_scaling = 1
        try:
            # _cmd = ["gsettings","get","org.gnome.desktop.interface","text-scaling-factor"]
            # text_scaling = subprocess.check_output(_cmd).decode().strip("\n")
            # text_scaling = int(float(text_scaling))
            _gsett = Gio.Settings.new("org.gnome.desktop.interface")
            _val = _gsett.get_double("text-scaling-factor")
            text_scaling = int(float(_val))
        except:
            text_scaling = 1
        return text_scaling
        
    def on_set_font_size(self, _term, _font_size, text_scaling):
        _font_desc = _term.get_font()
        if not _font_desc.get_size_is_absolute():
            return
        _font_desc.set_absolute_size(_font_size*text_scaling*1.33333333333333*Pango.SCALE)
        _term.set_font(_font_desc)
    
    def set_font_size(self, _font_size):
        n_pages = self._notebook.get_n_pages()
        text_scaling = self.get_font_scaling()
        for i in range(n_pages):
            _sw = self._notebook.get_nth_page(i)
            _term = _sw.terminal
            self.on_set_font_size(_term, _font_size, text_scaling)

a = Gdk.RGBA() # also background
a.alpha=1
a.blu=0.0
a.green=0.0
a.red=0.0
b = Gdk.RGBA()
b.alpha=1
b.blu=1.0
b.green=0.41
b.red=1.0
c = Gdk.RGBA() # prompt
c.alpha=1
c.blu=0.275
c.green=0.8
c.red=0.0
d = Gdk.RGBA()
d.alpha=1
d.blu=0.67
d.green=0.65
d.red=0.0
e = Gdk.RGBA() # path and folders
e.alpha=1
e.blu=0.44
e.green=0.61
e.red=1.0
f = Gdk.RGBA()# images videos
f.alpha=1
f.blu=0.85
f.green=0.41
f.red=0.96
g = Gdk.RGBA()
g.alpha=1
g.blu=0.0
g.green=0.72
g.red=0.75
h = Gdk.RGBA()# also foreground
h.alpha=1
h.blu=0.74
h.green=0.74
h.red=0.74
#
a2 = Gdk.RGBA()# backup files
a2.alpha=1
a2.blu=0.87
a2.green=0.87
a2.red=0.87
b2 = Gdk.RGBA()
b2.alpha=1
b2.blu=1.0
b2.green=0.7
b2.red=0.56
c2 = Gdk.RGBA()
c2.alpha=1
c2.blu=0.0
c2.green=0.93
c2.red=0.48
d2 = Gdk.RGBA()
d2.alpha=1
d2.blu=0.71
d2.green=0.85
d2.red=0.0
e2 = Gdk.RGBA() # path and folders?
e2.alpha=1
e2.blu=0.75
e2.green=0.75
e2.red=1.0
f2 = Gdk.RGBA()
f2.alpha=1
f2.blu=1.0
f2.green=0.65
f2.red=0.875
g2 = Gdk.RGBA()
g2.alpha=1
g2.blu=0.235
g2.green=0.86
g2.red=1.0
h2 = Gdk.RGBA() # also foreground
h2.alpha=1
h2.blu=1.0
h2.green=1.0
h2.red=1.0
#
term_palette = [a,b,c,d,e,f,g,h,a2,b2,c2,d2,e2,f2,g2,h2]

"""
GdkRGBA my_palette[16] = {
    { 0.0, 0.0, 0.0, 1.0 }, // 0: Black
    { 0.8, 0.2, 0.2, 1.0 }, // 1: Red
    { 0.2, 0.8, 0.2, 1.0 }, // 2: Green
    { 0.8, 0.8, 0.2, 1.0 }, // 3: Yellow
    { 0.2, 0.2, 0.8, 1.0 }, // 4: Blue
    { 0.8, 0.2, 0.8, 1.0 }, // 5: Magenta
    { 0.2, 0.8, 0.8, 1.0 }, // 6: Cyan
    { 0.9, 0.9, 0.9, 1.0 }, // 7: White
    // --- Colori Bright (8-15) ---
    { 0.3, 0.3, 0.3, 1.0 }, // 8: Bright Black
    { 1.0, 0.3, 0.3, 1.0 }, // 9: Bright Red
    { 0.3, 1.0, 0.3, 1.0 }, // 10: Bright Green
    { 1.0, 1.0, 0.3, 1.0 }, // 11: Bright Yellow
    { 0.3, 0.3, 1.0, 1.0 }, // 12: Bright Blue
    { 1.0, 0.3, 1.0, 1.0 }, // 13: Bright Magenta
    { 0.3, 1.0, 1.0, 1.0 }, // 14: Bright Cyan
    { 1.0, 1.0, 1.0, 1.0 }  // 15: Bright White
};
"""


class ScrolWin(Gtk.ScrolledWindow):
    def __init__(self, _parent, _path):
        super().__init__()
        self.main_app = _parent
        self._path = _path
        #
        self.set_hexpand(True)
        self.set_vexpand(True)
        self.propagate_natural_height = 1
        self.propagate_natural_width = 1
        #
        self.terminal = Vte.Terminal.new()
        self.set_child(self.terminal)
        #
        _color_fore = Gdk.RGBA()
        _color_fore.parse(FOREGROUND_COLOR)
        self.terminal.set_colors(_color_fore, None, term_palette)
        #
        self.terminal.set_enable_bidi(True)
        self.terminal.set_enable_shaping(True)
        self.terminal.set_mouse_autohide(True)
        #
        self.set_context_menu()
        #
        self.terminal.connect("termprop-changed", self.on_termprop_changed)
        self.terminal.connect("decrease-font-size", self.on_font_changed, -1)
        self.terminal.connect("increase-font-size", self.on_font_changed, 1)
        self.terminal.connect("child-exited", self.on_child_exited)
        # self.terminal.connect("resize-window", self.on_terminal_resized)
        self.terminal.connect("realize", self.terminal_shown)
        #
        self.on_create_notebook_label(self._path)
        #
        global COMMANDLINE_PEXEC
        if COMMANDLINE_PEXEC and shutil.which(COMMANDLINE_PEXEC):
             _cmd = ["/usr/bin/bash", "-c", COMMANDLINE_PEXEC]
             COMMANDLINE_PEXEC = -1
        else:
            _cmd = ["/usr/bin/bash"]
        term_path = self._path
        if COMMANDLINE_PWD and COMMANDLINE_PEXEC == None:
            term_path = COMMANDLINE_PWD
        try:
            self.terminal.spawn_async(
                Vte.PtyFlags.DEFAULT,
                term_path,
                _cmd,
                None,  # inherit the parent environment
                GLib.SpawnFlags.DO_NOT_REAP_CHILD,
                None,  # child_setup
                None,  # child_setup_data
                -1, # timeout
                None, # cancellable
                self.ready,
                None)
        except Exception as E:
            AlDial(self_main, str(E))
        # grab the focus
        self.terminal.grab_focus()
    
    def ready(self, terminal, pid, error, user_data=None):
        terminal.pid = pid
        return
    
    def terminal_shown(self, _w):
        # setting the font size
        text_scaling = self.main_app.get_font_scaling()
        self.main_app.on_set_font_size(self.terminal, FONT_SIZE, text_scaling)
    
    def set_context_menu(self):
        # The main menu
        self.file_menu = Gio.Menu.new()
        action_group = Gio.SimpleActionGroup()
        self.insert_action_group('win', action_group)
        self.terminal.set_context_menu_model(self.file_menu)
        #
        if COMMANDLINE_PEXEC == None:
            self.file_menu.append(_lang.NEWTERM, 'win.NewTerm2')
            button_nt2 = Gio.SimpleAction(name="NewTerm2", parameter_type=None, enabled=True)
            button_nt2.connect("activate", self.on_new_term2)
            action_group.add_action(button_nt2)
        #
        self.file_menu.append(_lang.COPYVISIBLE, 'win.CopyVisible')
        button_cv2 = Gio.SimpleAction(name="CopyVisible", parameter_type=None, enabled=True)
        button_cv2.connect("activate", self.on_copy_visible)
        action_group.add_action(button_cv2)
        #
        self.file_menu.append(_lang.COPYSELECTION, 'win.CopySel')
        button_cs2 = Gio.SimpleAction(name="CopySel", parameter_type=None, enabled=True)
        button_cs2.connect("activate", self.on_copy_selection)
        action_group.add_action(button_cs2)
        #
        if COMMANDLINE_PEXEC == None:
            self.file_menu.append(_lang.PASTESELECTION, 'win.PasteSel')
            button_ps2 = Gio.SimpleAction(name="PasteSel", parameter_type=None, enabled=True)
            button_ps2.connect("activate", self.on_paste_selection)
            action_group.add_action(button_ps2)
        
    def on_new_term2(self, action, param):
        try:
            subprocess.Popen([os.path.join(HOME_CONFIG,"QuartzTE.sh"), "-w", self._path])
        except Exception as E:
            AlDial(self_main, str(E))
    
    def on_copy_selection(self, action, param):
        _text = self.terminal.get_text_selected(Vte.Format.TEXT)
        clipboard.set(_text)
        
    def on_copy_visible(self, action, param):
        _text = self.terminal.get_text_format(Vte.Format.TEXT)
        clipboard.set(_text)
        
    def on_paste_selection(self, action, param):
        def on_paste_text(_clipboard, _result):
            _text = None
            try:
                _text = _clipboard.read_text_finish(_result)
            except:
                _text = None
            if _text is not None:
                self.terminal.paste_text(_text)
        clipboard.read_text_async(None, on_paste_text)
        
    # def on_terminal_resized(self, terminal, rows, columns):
        # pass
    
    def on_termprop_changed(self, terminal, _prop):
        _name = terminal.get_termprop_string(_prop)
        self._lbl.set_label(_name[0])
        self._path = os.path.expanduser(_name[0].split(": ")[1])
        
    # _type: 1 increase - -1 decrease
    def on_font_changed(self, terminal, _type):
        if _type == -1 and self.terminal.get_font_scale() < 0.31:
            return
        self.terminal.set_font_scale(round(self.terminal.get_font_scale(), 2)+0.1*_type)
    
    def on_create_notebook_label(self, _file):
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        # 
        if self._path:
            self._lbl = Gtk.Label(label=os.path.basename(self._path))
        else:
            self._lbl = Gtk.Label(label="New Tab")
        #
        self._lbl.set_hexpand(True)
        box.append(self._lbl)
        self._label_tab = self._lbl
        # close button
        btn = Gtk.Button.new()
        if icon_theme.has_icon("gtk-close"):
            _btn_il = "gtk-close"
        elif icon_theme.has_icon("stock-close"):
            _btn_il = "stock-close"
        elif icon_theme.has_icon("close"):
            _btn_il = "close"
        elif icon_theme.has_icon("window-close"):
            _btn_il = "window-close"
        btn.set_icon_name(_btn_il)
        btn.connect("clicked", self.on_close_this)
        box.append(btn)
        self.tab_label = box
    
    def on_child_exited(self, terminal, _status):
        self.main_app.app_.quit()
        
    def on_close_this(self, w=None):
        ret = self.main_app.terminate_process(self.terminal.pid)
        if ret == 0:
            if self.main_app._notebook.get_n_pages() > 1:
                idx = self.main_app._notebook.get_current_page()
                self.main_app._notebook.remove_page(idx)
        elif ret == -1:
            AlDial(self_main, _lang.TMSG1)
            self.terminal.grab_focus()

class AlDial(Gtk.AlertDialog):
    def __init__(self, _parent, _str1):
        super().__init__()
        self._parent = _parent
        self._str1 = _str1
        #
        self.set_message(self._str1)
        #
        self.show(self._parent)

# yes/no dialog - close the application and check for modified files
class YNDial(Gtk.AlertDialog):
    def __init__(self, _parent, _str1, _str2):
        super().__init__()
        self._parent = _parent
        self._str1 = _str1
        self._str2 = _str2
        #
        self.set_buttons([_lang.YES, _lang.NO])
        self.props.cancel_button = 1
        #
        self.set_message(self._str1)
        self.set_detail(self._str2)
        #
        self.choose(self._parent, None, self._parent.dialog_action, None)

##################

class WinSettings(Gtk.Window):
    def __init__(self, _parent):
        super().__init__()
        self._parent = _parent
        self.set_transient_for(self._parent)
        self.set_destroy_with_parent(True)
        self.set_name("settingdialog")
        self.set_resizable(True)
        self.set_size_request(800, 300)
        self.set_title(_lang.FSETTINGS)
        self.set_icon_name("com.quartz.terminal.emulator")
        #
        self.headerbar = Gtk.HeaderBar.new()
        self.set_titlebar(self.headerbar)
        self.headerbar.set_show_title_buttons(False)
        #
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_child(self.main_box)
        #
        self.stack_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.main_box.append(self.stack_box)
        #
        self.stack_sidebar = Gtk.StackSidebar.new()
        self.stack_sidebar.set_vexpand(True)
        self.stack_box.append(self.stack_sidebar)
        #
        btn_apply = Gtk.Button(label=_lang.APPLY)
        btn_apply.connect("clicked", self.on_apply)
        self.headerbar.pack_start(btn_apply)
        #
        btn_close = Gtk.Button(label=_lang.CLOSE)
        btn_close.connect("clicked", self.on_close)
        self.headerbar.pack_end(btn_close)
        #
        self._stack = Gtk.Stack.new()
        self._stack.props.hexpand = True
        self._stack.props.vexpand = True
        self.stack_sidebar.set_stack(self._stack)
        self.stack_box.append(self._stack)
        ############
        box1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        #
        self._stack.add_titled(box1,"box1",_lang.PGENERAL)
        bgrid1 = Gtk.Grid.new()
        bgrid1.set_column_homogeneous(False)
        bgrid1.set_hexpand(True)
        bgrid1.set_vexpand(True)
        box1.append(bgrid1)
        # font size
        lbl00 = Gtk.Label(label=_lang.FONTSIZE)
        lbl00.set_halign(Gtk.Align.START)
        bgrid1.attach(lbl00,0,0,1,1)
        self.fontsize_spinbtn = Gtk.SpinButton.new_with_range(4,80,1)
        self.fontsize_spinbtn.set_value(FONT_SIZE)
        bgrid1.attach_next_to(self.fontsize_spinbtn,lbl00,1,1,1)
        # font family
        lbl02 = Gtk.Label(label=_lang.FONTFAMILY)
        lbl02.set_halign(Gtk.Align.START)
        bgrid1.attach(lbl02,0,2,1,1)
        self.fontfamily_btn = Gtk.Button(label=FONT_FAMILY)
        self.fontfamily_btn.connect("clicked", self.on_font_family)
        bgrid1.attach_next_to(self.fontfamily_btn,lbl02,1,1,1)
        self.new_font_family = None
        # foreground color
        lbl01 = Gtk.Label(label=_lang.FOREGROUNDCOLOR)
        lbl01.set_halign(Gtk.Align.START)
        bgrid1.attach(lbl01,0,3,1,1)
        color_dlg = Gtk.ColorDialog.new()
        self.fcolor_btn = Gtk.ColorDialogButton.new(color_dlg)
        _btn_color = Gdk.RGBA()
        _btn_color.parse(FOREGROUND_COLOR)
        self.fcolor_btn.set_rgba(_btn_color)
        bgrid1.attach_next_to(self.fcolor_btn,lbl01,1,1,1)
        #
        ########
        self.present()
    
    def on_font_family(self, _w):
        _fd = Gtk.FontDialog.new()
        def font_choosed(source_object, res, data):
            try:
                _pango_font_family = _fd.choose_family_finish(res)
            except GLib.GError:
                return
            _font_name = _pango_font_family.get_name()
            self.set_terminal_family(_font_name)
        _fd.choose_family(self, None, None, font_choosed, None)
        
    def set_terminal_family(self, _font_name):
        n_pages = self._parent._notebook.get_n_pages()
        for i in range(n_pages):
            _sw = self._parent._notebook.get_nth_page(i)
            _term = _sw.terminal
            _font_desc = _term.get_font()
            _font_desc.set_family(_font_name)
            _term.set_font(_font_desc)
        self.fontfamily_btn.set_label(_font_name)
        global FONT_FAMILY
        FONT_FAMILY = _font_name
    
    def set_foreground_color_globally(self):
        n_pages = self._parent._notebook.get_n_pages()
        for i in range(n_pages):
            _sw = self._parent._notebook.get_nth_page(i)
            _term = _sw.terminal
            _color_fore = Gdk.RGBA()
            _color_fore.parse(FOREGROUND_COLOR)
            _term.set_colors(_color_fore, None, term_palette)
    
    def on_apply(self, w):
        global WWIDTH
        global WHEIGHT
        global FOREGROUND_COLOR
        _sw = self._parent._notebook.get_nth_page(self._parent._notebook.get_current_page())
        #
        WWIDTH = self._parent.get_width()
        config_conf["wwidth"] = self._parent.get_width()
        WHEIGHT = self._parent.get_height()
        config_conf["wheight"] = self._parent.get_height()
        #
        FONT_SIZE = int(self.fontsize_spinbtn.get_value())
        config_conf["font-size"] = FONT_SIZE
        self._parent.set_font_size(FONT_SIZE)
        #
        FOREGROUND_COLOR = self.fcolor_btn.get_rgba().to_string()
        config_conf["foreground-color"] = FOREGROUND_COLOR
        self.set_foreground_color_globally()
        #
        config_conf["font-family"] = FONT_FAMILY
        try:
            _ff =  open(os.path.join(HOME_CONFIG,"configs/config.json"), "w")
            json.dump(config_conf, _ff, indent = 4)
            _ff.close()
        except Exception as E:
            AlDial(self_main, str(E))
        #
        self.destroy()
        _sw.terminal.grab_focus()
    
    def on_close(self, w):
        self.destroy()
        _sw = self._parent._notebook.get_nth_page(self._parent._notebook.get_current_page())
        _sw.terminal.grab_focus()


class MyApp(Gtk.Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        _e2 = GLib.OptionEntry()
        _e2.arg=GLib.OptionArg.NONE
        _e2.arg_data=None
        _e2.arg_description="File path"
        _e2.description="Working directory"
        _e2.flags=GLib.OptionFlags.FILENAME
        _e2.long_name="working-directory"
        _e2.short_name=ord("w")
        self.add_main_option_entries([_e2])
        #
        _e3 = GLib.OptionEntry()
        _e3.arg=int(GLib.OptionArg.NONE)
        _e3.arg_data=None
        _e3.arg_description=None
        _e3.description="Execute a shell program"
        _e3.flags=GLib.OptionFlags.NONE
        _e3.long_name="execute"
        _e3.short_name=ord("e")
        self.add_main_option_entries([_e3])
        #
        self._files = None
        self.n_files = None
            
    def do_activate(self):
        active_window = self.props.active_window
        self.win = MainWindow(application=self, _files=self._files, n_files=self.n_files)
        self.win.present()
    
    def do_command_line(self, command_line):
        global SINGLE_APP
        active_window = self.props.active_window
        options = command_line.get_options_dict()
        options = options.end().unpack()
        global COMMANDLINE_PEXEC
        if "execute" in options and COMMANDLINE_PEXEC != -1:
            for el in command_line.get_arguments()[1:]:
                if shutil.which(el):
                    COMMANDLINE_PEXEC = el
                    break
            if COMMANDLINE_PEXEC:
                self.win = MainWindow(application=self, _files=None, n_files=self.n_files)
                self.win.present()
        elif "working-directory" in options:
            for el in command_line.get_arguments()[1:]:
                if os.path.exists(el) and os.path.isdir(el):
                    global COMMANDLINE_PWD
                    COMMANDLINE_PWD = el
                    break
            if COMMANDLINE_PWD:
                self.win = MainWindow(application=self, _files=[Gio.File.new_for_path(COMMANDLINE_PWD)], n_files=self.n_files)
                self.win.present()
        else:
            active_window = self.props.active_window
            if active_window:
                args = command_line.get_arguments()
                COMMANDLINE_CWD = command_line.get_cwd()
                try:
                    subprocess.Popen([os.path.join(COMMANDLINE_CWD,"QuartzTE.sh")])
                except:
                    pass
                return 0
            else:
                self.win = MainWindow(application=self, _files=self._files, n_files=self.n_files)
                self.win.present()
        return 0

################

app = MyApp(application_id="com.quartz.terminal.emulator",flags= Gio.ApplicationFlags.HANDLES_COMMAND_LINE|Gio.ApplicationFlags.NON_UNIQUE)
app.run(sys.argv)
