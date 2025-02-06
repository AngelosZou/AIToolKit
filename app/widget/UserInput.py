from textual.widgets import Input, TextArea


class UserInput(TextArea):
    def _on_key(self, event):
        # Shift+Enter 换行，Enter 发送
        if event.key == "enter":
            event.prevent_default().stop()
            self.insert("\n")