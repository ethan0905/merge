# macos_agent_ui.py
#
# Single-line ChatGPT input bar — draggable pill — ⌘⇧C toggle with corrected shortcuts — hidden focus ring.
# -----------------------------------------------------------------------------------
# Fixes in this revision (r13):
#   • **Hide focus ring**: Disabled the default focus ring on NSTextField.
#   • **Fix shortcut**: Use NSEventTypeKeyDown (not mask) for event comparison.
# -----------------------------------------------------------------------------------

from Cocoa import (
    NSApplication,
    NSApp,
    NSObject,
    NSWindow,
    NSWindowStyleMaskBorderless,
    NSWindowStyleMaskFullSizeContentView,
    NSBackingStoreBuffered,
    NSMakeRect,
    NSColor,
    NSVisualEffectMaterialSidebar,
    NSVisualEffectBlendingModeBehindWindow,
    NSVisualEffectStateActive,
    NSFont,
    NSTextField,
    NSFocusRingTypeNone,
    NSButton,
    NSViewWidthSizable,
    NSVisualEffectView,
    NSEvent,
    NSEventMaskKeyDown,
    NSEventTypeKeyDown,
    NSEventModifierFlagCommand,
    NSEventModifierFlagShift,
)
from PyObjCTools import AppHelper
import objc


# ---------------------------------------------------------------------------
# Helper: Draggable, vibrant background view
# ---------------------------------------------------------------------------
class DraggableVibrantView(NSVisualEffectView):
    def mouseDown_(self, event):
        self.window().performWindowDragWithEvent_(event)


# ---------------------------------------------------------------------------
# ChatAgentWindow
# ---------------------------------------------------------------------------
class ChatAgentWindow(NSWindow):
    BAR_HEIGHT = 40
    ARROW_SIZE = 28
    MARGIN = 14

    def canBecomeKeyWindow(self):
        return True

    def canBecomeMainWindow(self):
        return True

    def init(self):
        frame = NSMakeRect(0, 0, 520, self.BAR_HEIGHT)
        style = NSWindowStyleMaskBorderless | NSWindowStyleMaskFullSizeContentView
        self = objc.super(ChatAgentWindow, self).initWithContentRect_styleMask_backing_defer_(
            frame, style, NSBackingStoreBuffered, False
        )
        if self is None:
            return None

        # Window basics
        self.setOpaque_(False)
        self.setBackgroundColor_(NSColor.clearColor())
        self.setMovableByWindowBackground_(True)
        # Rounded pill corners
        self.contentView().setWantsLayer_(True)
        self.contentView().layer().setCornerRadius_(self.BAR_HEIGHT / 2)
        self.contentView().layer().setMasksToBounds_(True)

        # Vibrant blur background
        vibrant = DraggableVibrantView.alloc().initWithFrame_(self.contentView().bounds())
        vibrant.setAutoresizingMask_(NSViewWidthSizable)
        vibrant.setMaterial_(NSVisualEffectMaterialSidebar)
        vibrant.setBlendingMode_(NSVisualEffectBlendingModeBehindWindow)
        vibrant.setState_(NSVisualEffectStateActive)
        self.contentView().addSubview_(vibrant)

        # Font + baseline
        font = NSFont.systemFontOfSize_(14)
        line_height = font.defaultLineHeightForFont() + 2
        input_y = (self.BAR_HEIGHT - line_height) / 2

        # Text field
        input_rect = NSMakeRect(
            self.MARGIN,
            input_y,
            frame.size.width - self.ARROW_SIZE - 1 * self.MARGIN,
            line_height,
        )
        input_field = NSTextField.alloc().initWithFrame_(input_rect)
        input_field.setPlaceholderString_("Type your computer-agent request here…")
        input_field.setUsesSingleLineMode_(True)
        input_field.setBezeled_(False)
        input_field.setBordered_(False)
        input_field.setDrawsBackground_(False)
        input_field.setEditable_(True)
        input_field.setSelectable_(True)
        input_field.setFocusRingType_(NSFocusRingTypeNone)  # hide focus ring
        input_field.setFont_(font)
        vibrant.addSubview_(input_field)

        # Arrow button
        arrow_x = frame.size.width - self.ARROW_SIZE - 6
        arrow_y = (self.BAR_HEIGHT - self.ARROW_SIZE) / 2
        send_btn = NSButton.alloc().initWithFrame_(
            NSMakeRect(arrow_x, arrow_y, self.ARROW_SIZE, self.ARROW_SIZE)
        )
        send_btn.setTitle_("↑")
        send_btn.setBordered_(False)
        send_btn.setFont_(NSFont.boldSystemFontOfSize_(18))
        send_btn.setContentTintColor_(NSColor.darkGrayColor())
        send_btn.setBackgroundColor_(NSColor.whiteColor())
        send_btn.setCornerRadius_(self.ARROW_SIZE / 2)
        vibrant.addSubview_(send_btn)

        # Events
        input_field.setTarget_(self)
        input_field.setAction_("submit:")
        send_btn.setTarget_(self)
        send_btn.setAction_("submit:")

        self.input_field = input_field
        return self

    def submit_(self, _):
        txt = self.input_field.stringValue().strip()
        if not txt:
            return
        print("You:", txt)
        self.input_field.setStringValue_("")
        # TODO: hook up LLM call here


# ---------------------------------------------------------------------------
# AppDelegate with ⌘⇧C shortcut
# ---------------------------------------------------------------------------
class AppDelegate(NSObject):
    def applicationDidFinishLaunching_(self, _):
        self.window = ChatAgentWindow.alloc().init()
        self.window.center()
        self.window.makeKeyAndOrderFront_(None)
        NSApp.activateIgnoringOtherApps_(True)
        self.window.makeFirstResponder_(self.window.input_field)

        self._install_shortcut()

    def _install_shortcut(self):
        flags_required = NSEventModifierFlagCommand | NSEventModifierFlagShift

        def handler(event):
            if (
                event.type() == NSEventTypeKeyDown
                and event.charactersIgnoringModifiers().lower() == "c"
                and (event.modifierFlags() & flags_required) == flags_required
            ):
                self.toggleWindow()
            return event

        NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(NSEventMaskKeyDown, handler)
        NSEvent.addLocalMonitorForEventsMatchingMask_handler_(NSEventMaskKeyDown, handler)

    def toggleWindow(self):
        if self.window.isVisible():
            self.window.orderOut_(None)
        else:
            self.window.center()
            self.window.makeKeyAndOrderFront_(None)
            NSApp.activateIgnoringOtherApps_(True)
            self.window.makeFirstResponder_(self.window.input_field)


if __name__ == '__main__':
    app = NSApplication.sharedApplication()
    delegate = AppDelegate.alloc().init()
    app.setDelegate_(delegate)
    AppHelper.runEventLoop()
