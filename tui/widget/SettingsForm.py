from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, Grid, VerticalScroll
from textual.validation import Number, Length
from textual.widgets import Select, Input, Label, Button
from textual.widgets._select import BLANK

from core.cache import Configure
from core.source.sources import SourceRegistry


class SettingsForm(VerticalScroll):
    """设置表单组件"""
    """设置表单组件（优化布局版）"""


    def __init__(self):
        super().__init__(id="settings-container")
        self.config = Configure.get_instance()
        self.source_registry = SourceRegistry.sources

    def compose(self) -> ComposeResult:
        # 获取当前配置
        config = self.config

        # AI源选择
        ai_options = [(key, key) for key in self.source_registry.keys()]
        yield Horizontal(
            Label("AI 源:"),
            Select(
                ai_options,
                prompt="选择AI源",
                value=config.active_ai if config.active_ai else BLANK,
                id="ai-source"
            ),
            classes="setting-item"
        )

        # 模型选择
        yield Horizontal(
            Label("模型名称:"),
            Input(
                value=self.get_current_model(),
                placeholder="输入模型名称",
                id="model-input"
            ),
            classes="setting-item"
        )

        # API密钥相关字段
        api_fields = [
            ("Google API Key", "google_api_key", config.google_api_key),
            ("OpenAI API Key", "openai_api_key", config.openai_api_key),
            ("SiliconFlow API Key", "siliconflow_api_key", config.siliconflow_api_key),
            ("Deepseek API Key", "deepseek_api_key", config.deepseek_api_key),
            ("Google CSE ID", "google_cse_id", config.google_cse_id)
        ]

        for label, field, value in api_fields:
            yield Horizontal(
                Label(f"{label}:"),
                Input(
                    value=value or "",
                    password=field.endswith("_key"),  # API密钥字段用密码输入
                    id=field
                ),
                classes="setting-item"
            )

        # 最大跳过输入轮次
        yield Horizontal(
            Label("最大跳过轮次:"),
            Input(
                str(config.max_skip_input_turn),
                placeholder="-1表示无限制",
                validators=[Number(minimum=-1)],
                type="integer",
                id="max-skip-input"
            ),
            classes="setting-item"
        )

    def get_current_model(self) -> str:
        """获取当前AI源对应的模型名称"""
        if not self.config.active_ai:
            return ""
        return self.config.active_model.get(self.config.active_ai, "")

    @on(Select.Changed, "#ai-source")
    def on_ai_source_changed(self, event: Select.Changed):
        """AI源改变时更新模型相关提示"""
        # 清空当前输入
        model_input = self.query_one("#model-input")
        model_input.value = self.config.active_model.get(event.value, "")

    @on(Input.Submitted, "#model-input")
    def on_model_submitted(self, event: Input.Submitted):
        """实时验证模型名称"""
        if not event.validation_result.is_valid:
            self.notify("模型名称验证失败：" + "\n".join(event.validation_result.failure_descriptions))

    # @on(Button.Pressed, "#save-settings")
    def save_settings(self):
        """保存设置"""
        try:
            config = self.config

            # 验证并保存字段
            config.active_ai = self.query_one("#ai-source").value
            config.active_model[config.active_ai] = self.query_one("#model-input").value

            # 保存API相关字段
            api_fields = [
                "google_api_key", "openai_api_key",
                "siliconflow_api_key", "deepseek_api_key",
                "google_cse_id"
            ]
            for field in api_fields:
                setattr(config, field, self.query_one(f"#{field}").value)

            # 保存最大跳过轮次
            max_skip = self.query_one("#max-skip-input").value
            config.max_skip_input_turn = int(max_skip) if max_skip else -1

            config.save()

        except ValueError as e:
            self.notify(f"保存失败: {str(e)}", severity="error")
