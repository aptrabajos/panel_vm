#!/usr/bin/env python3

import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GLib, Gio
import sys
import os

from vm_manager import VMManager
from ui import VMPanelWindow

class VMPanelApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id='com.manjaro.vmpanel')
        self.create_action('quit', self.quit, ['<primary>q'])

    def do_activate(self):
        win = self.props.active_window
        if not win:
            win = VMPanelWindow(application=self)
        win.present()

    def create_action(self, name, callback, shortcuts=None):
        action = Gio.SimpleAction.new(name, None)
        action.connect('activate', callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f'app.{name}', shortcuts)

def main():
    app = VMPanelApp()
    return app.run(sys.argv)

if __name__ == '__main__':
    main()