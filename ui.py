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
    NSProgressIndicator,
    NSProgressIndicatorStyleSpinning,
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
    STATUS_HEIGHT = 24

    def canBecomeKeyWindow(self):
        return True

    def canBecomeMainWindow(self):
        return True

    def init(self):
        frame = NSMakeRect(0, 0, 520, self.BAR_HEIGHT + self.STATUS_HEIGHT)
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

        # Vibrant blur background for the input area
        vibrant = DraggableVibrantView.alloc().initWithFrame_(
            NSMakeRect(0, self.STATUS_HEIGHT, frame.size.width, self.BAR_HEIGHT)
        )
        vibrant.setAutoresizingMask_(NSViewWidthSizable)
        vibrant.setMaterial_(NSVisualEffectMaterialSidebar)
        vibrant.setBlendingMode_(NSVisualEffectBlendingModeBehindWindow)
        vibrant.setState_(NSVisualEffectStateActive)
        self.contentView().addSubview_(vibrant)

        # Font + baseline
        font = NSFont.systemFontOfSize_(14)
        line_height = font.defaultLineHeightForFont() + 2
        input_y = self.STATUS_HEIGHT + (self.BAR_HEIGHT - line_height) / 2

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
        arrow_y = self.STATUS_HEIGHT + (self.BAR_HEIGHT - self.ARROW_SIZE) / 2
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

        spinner = NSProgressIndicator.alloc().initWithFrame_(
            NSMakeRect(arrow_x, arrow_y, self.ARROW_SIZE, self.ARROW_SIZE)
        )
        spinner.setStyle_(NSProgressIndicatorStyleSpinning)
        spinner.setDisplayedWhenStopped_(False)
        spinner.setHidden_(True)
        vibrant.addSubview_(spinner)

        status_lbl = NSTextField.alloc().initWithFrame_(
            NSMakeRect(self.MARGIN, 2, frame.size.width - 2 * self.MARGIN - 60, self.STATUS_HEIGHT - 4)
        )
        status_lbl.setEditable_(False)
        status_lbl.setBezeled_(False)
        status_lbl.setDrawsBackground_(False)
        status_lbl.setHidden_(True)
        self.contentView().addSubview_(status_lbl)

        up_btn = NSButton.alloc().initWithFrame_(
            NSMakeRect(frame.size.width - self.MARGIN - 50, 2, 20, self.STATUS_HEIGHT - 4)
        )
        up_btn.setTitle_("👍")
        up_btn.setBordered_(False)
        up_btn.setHidden_(True)
        self.contentView().addSubview_(up_btn)

        down_btn = NSButton.alloc().initWithFrame_(
            NSMakeRect(frame.size.width - self.MARGIN - 25, 2, 20, self.STATUS_HEIGHT - 4)
        )
        down_btn.setTitle_("👎")
        down_btn.setBordered_(False)
        down_btn.setHidden_(True)
        self.contentView().addSubview_(down_btn)

        # Events
        input_field.setTarget_(self)
        input_field.setAction_("submit:")
        send_btn.setTarget_(self)
        send_btn.setAction_("submit:")

        self.input_field = input_field
        self.send_btn = send_btn
        self.spinner = spinner
        self.status_lbl = status_lbl
        self.up_btn = up_btn
        self.down_btn = down_btn
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
