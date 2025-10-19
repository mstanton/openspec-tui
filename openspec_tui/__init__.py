"""
OpenSpec TUI Editor - A Textual-based interface for creating and editing OpenSpec templates

Installation:
    pip install textual

Usage:
    python openspec_tui.py
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import (
    Header, Footer, Button, Input, TextArea, Label, 
    Static, TabbedContent, TabPane, DataTable, Select,
    Checkbox, RadioSet, RadioButton
)
from textual.binding import Binding
from textual.screen import Screen
from textual import on
from pathlib import Path
import json
from datetime import datetime

# Templates
PROPOSAL_TEMPLATE = """# Proposal: {name}

## Overview

[1-2 paragraph summary of what this change does and why it matters]

## Problem Statement

[Describe the problem or need this change addresses]

**Current State:**
[What exists today and its limitations]

**Pain Points:**
- [Pain point 1]
- [Pain point 2]
- [Pain point 3]

## Proposed Solution

[High-level description of the solution]

**Key Changes:**
- [Major change 1]
- [Major change 2]
- [Major change 3]

## Scope

**In Scope:**
- [What this change includes]

**Out of Scope:**
- [What this deliberately excludes]

## Success Criteria

**This change is successful when:**
- [ ] [Measurable criterion 1]
- [ ] [Measurable criterion 2]

**Metrics to track:**
- [Metric 1]: Target [value]

## Timeline

**Estimated effort:** [X days/weeks]

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| [Risk 1] | High/Med/Low | [How to address] |
"""

TASKS_TEMPLATE = """# Implementation Tasks: {name}

## Overview

[Brief summary of the implementation approach]

---

## 1. [Phase/Component Name]

**Goal:** [What this phase accomplishes]

- [ ] **1.1** [Specific task]
  - Files: `path/to/file.ts`
  - Details: [Any specific implementation notes]
  - Acceptance: [How to verify completion]

---

## 2. Testing & Validation

**Goal:** Ensure all requirements are met

- [ ] **2.1** Write unit tests
  - Coverage: [Specific scenarios]
  - Files: `path/to/test.spec.ts`
"""

SPEC_TEMPLATE = """# {feature_area} Specification Delta

> **Note:** This is a spec delta for the `{name}` change.
> It will be merged into `openspec/specs/{feature_area}/spec.md` after approval.

---

## ADDED Requirements

### Requirement: [Requirement Name]

The system SHALL [action or behavior].

#### Scenario: [Scenario Name]

- **GIVEN** [precondition]
- **WHEN** [action or trigger]
- **THEN** [expected outcome]

**Acceptance Criteria:**
- [ ] [Testable criterion 1]

**Priority:** P0 / P1 / P2

---

## MODIFIED Requirements

[Leave empty if no modifications]

---

## REMOVED Requirements

[Leave empty if no removals]
"""

DESIGN_TEMPLATE = """# Design Document: {name}

## Technical Overview

[High-level technical summary of the solution]

---

## Architecture

### System Architecture

[Diagram or description of how components interact]

### Components

**Component 1: [Name]**
- **Purpose:** [What it does]
- **Responsibilities:** [Key functions]

---

## Data Model

### Database Schema Changes

[Describe schema changes]

---

## API Design

### New Endpoints

**POST /api/v1/[resource]**

Request:
```json
{{
  "field1": "string"
}}
```

---

## Security Considerations

[Security requirements and measures]

---

## Performance Considerations

**Expected Load:**
- Concurrent users: [Number]
- Requests per second: [Number]
"""


class NewChangeScreen(Screen):
    """Screen for creating a new OpenSpec change."""
    
    CSS = """
    NewChangeScreen {
        align: center middle;
    }
    
    #dialog {
        width: 80;
        height: auto;
        border: thick $background 80%;
        background: $surface;
        padding: 1 2;
    }
    
    .form-row {
        height: auto;
        margin: 1 0;
    }
    
    Label {
        width: 20;
        padding: 1 0;
    }
    
    Input {
        width: 1fr;
    }
    
    Select {
        width: 1fr;
    }
    
    .button-row {
        height: auto;
        align: center middle;
        margin-top: 2;
    }
    
    Button {
        margin: 0 1;
    }
    """
    
    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("Create New OpenSpec Change", classes="title")
            
            with Horizontal(classes="form-row"):
                yield Label("Change Name:")
                yield Input(placeholder="add-user-profile", id="change_name")
            
            with Horizontal(classes="form-row"):
                yield Label("Feature Area:")
                yield Input(placeholder="auth, profile, api", id="feature_area")
            
            with Horizontal(classes="form-row"):
                yield Label("Author:")
                yield Input(placeholder="Your Name", id="author")
            
            with Horizontal(classes="form-row"):
                yield Label("Include Design:")
                yield Checkbox("Generate design.md", id="include_design", value=True)
            
            with Horizontal(classes="button-row"):
                yield Button("Create", variant="primary", id="create_btn")
                yield Button("Cancel", variant="default", id="cancel_btn")
    
    @on(Button.Pressed, "#create_btn")
    def create_change(self):
        change_name = self.query_one("#change_name", Input).value
        feature_area = self.query_one("#feature_area", Input).value
        author = self.query_one("#author", Input).value
        include_design = self.query_one("#include_design", Checkbox).value
        
        if not change_name or not feature_area:
            self.notify("Change name and feature area are required", severity="error")
            return
        
        change_data = {
            "name": change_name,
            "feature_area": feature_area,
            "author": author,
            "include_design": include_design,
            "created_at": datetime.now().isoformat()
        }
        
        self.dismiss(change_data)
    
    @on(Button.Pressed, "#cancel_btn")
    def cancel(self):
        self.dismiss(None)


class TaskEditor(Container):
    """Widget for editing tasks with checkboxes."""
    
    CSS = """
    TaskEditor {
        height: auto;
        padding: 1;
        border: solid $primary;
    }
    
    .task-header {
        height: auto;
        margin-bottom: 1;
    }
    
    .task-row {
        height: auto;
        margin: 0 0 1 0;
    }
    """
    
    def __init__(self, phase_name: str = "Phase 1", **kwargs):
        super().__init__(**kwargs)
        self.phase_name = phase_name
        self.tasks = []
    
    def compose(self) -> ComposeResult:
        with Vertical(classes="task-header"):
            yield Label(f"## {self.phase_name}", markup=True)
            yield Input(placeholder="Phase goal...", id=f"goal_{self.id}")
        
        yield Button("+ Add Task", id=f"add_task_{self.id}", variant="primary")
    
    def add_task(self, task_id: str = "1.1", description: str = "", completed: bool = False):
        """Add a new task to the editor."""
        task_container = Horizontal(classes="task-row")
        checkbox = Checkbox(value=completed, id=f"check_{task_id}")
        input_field = Input(value=description, placeholder=f"Task {task_id} description")
        
        self.mount(task_container)
        task_container.mount(checkbox)
        task_container.mount(input_field)
        
        self.tasks.append({
            "id": task_id,
            "description": description,
            "completed": completed
        })


class EditorScreen(Screen):
    """Main editor screen for OpenSpec change."""
    
    BINDINGS = [
        Binding("ctrl+s", "save", "Save"),
        Binding("ctrl+q", "quit", "Quit"),
        Binding("ctrl+p", "preview", "Preview"),
    ]
    
    CSS = """
    EditorScreen {
        layout: vertical;
    }
    
    #info-bar {
        dock: top;
        height: 3;
        background: $primary;
        color: $text;
        padding: 1;
    }
    
    #content {
        height: 1fr;
    }
    
    TextArea {
        height: 1fr;
    }
    
    .status-label {
        margin: 0 1;
    }
    """
    
    def __init__(self, change_data: dict, **kwargs):
        super().__init__(**kwargs)
        self.change_data = change_data
        self.current_file = "proposal"
        self.files = {}
        self._init_files()
    
    def _init_files(self):
        """Initialize file contents from templates."""
        name = self.change_data["name"]
        feature_area = self.change_data["feature_area"]
        
        self.files = {
            "proposal": PROPOSAL_TEMPLATE.format(name=name.replace("-", " ").title()),
            "tasks": TASKS_TEMPLATE.format(name=name.replace("-", " ").title()),
            "spec": SPEC_TEMPLATE.format(name=name, feature_area=feature_area)
        }
        
        if self.change_data.get("include_design", False):
            self.files["design"] = DESIGN_TEMPLATE.format(name=name.replace("-", " ").title())
    
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        
        with Horizontal(id="info-bar"):
            yield Label(f"[bold]Change:[/bold] {self.change_data['name']}", classes="status-label")
            yield Label(f"[bold]Feature:[/bold] {self.change_data['feature_area']}", classes="status-label")
            yield Label(f"[bold]Author:[/bold] {self.change_data.get('author', 'Unknown')}", classes="status-label")
        
        with TabbedContent(id="content"):
            with TabPane("Proposal", id="tab_proposal"):
                yield TextArea(
                    self.files["proposal"],
                    language="markdown",
                    theme="dracula",
                    id="editor_proposal"
                )
            
            with TabPane("Tasks", id="tab_tasks"):
                yield TextArea(
                    self.files["tasks"],
                    language="markdown",
                    theme="dracula",
                    id="editor_tasks"
                )
            
            with TabPane("Spec Delta", id="tab_spec"):
                yield TextArea(
                    self.files["spec"],
                    language="markdown",
                    theme="dracula",
                    id="editor_spec"
                )
            
            if "design" in self.files:
                with TabPane("Design", id="tab_design"):
                    yield TextArea(
                        self.files["design"],
                        language="markdown",
                        theme="dracula",
                        id="editor_design"
                    )
        
        yield Footer()
    
    def action_save(self):
        """Save all files to disk."""
        base_path = Path(f"openspec/changes/{self.change_data['name']}")
        base_path.mkdir(parents=True, exist_ok=True)
        
        # Save metadata
        with open(base_path / "metadata.json", "w") as f:
            json.dump(self.change_data, f, indent=2)
        
        # Save proposal
        proposal_text = self.query_one("#editor_proposal", TextArea).text
        with open(base_path / "proposal.md", "w") as f:
            f.write(proposal_text)
        
        # Save tasks
        tasks_text = self.query_one("#editor_tasks", TextArea).text
        with open(base_path / "tasks.md", "w") as f:
            f.write(tasks_text)
        
        # Save spec
        spec_path = base_path / "specs" / self.change_data["feature_area"]
        spec_path.mkdir(parents=True, exist_ok=True)
        spec_text = self.query_one("#editor_spec", TextArea).text
        with open(spec_path / "spec.md", "w") as f:
            f.write(spec_text)
        
        # Save design if included
        if "design" in self.files:
            design_text = self.query_one("#editor_design", TextArea).text
            with open(base_path / "design.md", "w") as f:
                f.write(design_text)
        
        self.notify(f"✓ Saved to {base_path}", severity="information")
    
    def action_quit(self):
        """Quit the editor."""
        self.app.pop_screen()
    
    def action_preview(self):
        """Show preview of current file."""
        tabs = self.query_one(TabbedContent)
        active_tab = tabs.active
        
        if active_tab.startswith("tab_"):
            file_name = active_tab[4:]
            editor_id = f"editor_{file_name}"
            try:
                editor = self.query_one(f"#{editor_id}", TextArea)
                content = editor.text
                self.notify(f"Preview: {len(content)} characters", severity="information")
            except:
                pass


class MainScreen(Screen):
    """Main menu screen."""
    
    CSS = """
    MainScreen {
        align: center middle;
    }
    
    #menu {
        width: 60;
        height: auto;
        border: thick $background 80%;
        background: $surface;
        padding: 2;
    }
    
    .title {
        text-align: center;
        text-style: bold;
        margin-bottom: 2;
        color: $accent;
    }
    
    .subtitle {
        text-align: center;
        margin-bottom: 3;
        color: $text-muted;
    }
    
    Button {
        width: 100%;
        margin: 1 0;
    }
    
    .changes-list {
        height: auto;
        max-height: 15;
        margin: 2 0;
        border: solid $primary;
        padding: 1;
    }
    """
    
    def compose(self) -> ComposeResult:
        with Vertical(id="menu"):
            yield Label("OpenSpec TUI Editor", classes="title")
            yield Label("Spec-driven development for AI coding assistants", classes="subtitle")
            
            yield Button("🆕 Create New Change", id="new_change", variant="primary")
            yield Button("📂 Open Existing Change", id="open_change", variant="default")
            yield Button("📋 List Changes", id="list_changes", variant="default")
            yield Button("ℹ️  About OpenSpec", id="about", variant="default")
            yield Button("🚪 Exit", id="exit", variant="error")
            
            with VerticalScroll(classes="changes-list"):
                yield Label("[dim]Recent changes will appear here[/dim]", id="recent_changes")
    
    def on_mount(self):
        """Load recent changes on mount."""
        self._load_recent_changes()
    
    def _load_recent_changes(self):
        """Load list of recent changes from filesystem."""
        changes_dir = Path("openspec/changes")
        if changes_dir.exists():
            changes = []
            for change_dir in changes_dir.iterdir():
                if change_dir.is_dir():
                    metadata_file = change_dir / "metadata.json"
                    if metadata_file.exists():
                        with open(metadata_file) as f:
                            metadata = json.load(f)
                            changes.append(f"• {metadata['name']} ({metadata.get('feature_area', 'unknown')})")
            
            if changes:
                recent_label = self.query_one("#recent_changes", Label)
                recent_label.update("\n".join(changes[:10]))
    
    @on(Button.Pressed, "#new_change")
    async def new_change(self):
        """Create a new change."""
        result = await self.app.push_screen_wait(NewChangeScreen())
        if result:
            self.app.push_screen(EditorScreen(result))
    
    @on(Button.Pressed, "#open_change")
    def open_change(self):
        """Open existing change."""
        self.notify("Feature coming soon: Browse and open existing changes", severity="warning")
    
    @on(Button.Pressed, "#list_changes")
    def list_changes(self):
        """List all changes."""
        changes_dir = Path("openspec/changes")
        if not changes_dir.exists():
            self.notify("No changes directory found. Create a change first!", severity="warning")
            return
        
        changes = list(changes_dir.iterdir())
        if changes:
            self.notify(f"Found {len(changes)} change(s) in openspec/changes/", severity="information")
        else:
            self.notify("No changes found", severity="warning")
    
    @on(Button.Pressed, "#about")
    def about(self):
        """Show about information."""
        about_text = """
OpenSpec aligns humans and AI coding assistants with spec-driven development.

Key Features:
• Structured change proposals
• Task-based implementation
• Spec deltas (ADDED/MODIFIED/REMOVED)
• AI-native workflow

Learn more: github.com/Fission-AI/OpenSpec
        """
        self.notify(about_text.strip(), timeout=10)
    
    @on(Button.Pressed, "#exit")
    def exit_app(self):
        """Exit the application."""
        self.app.exit()


class OpenSpecTUI(App):
    """OpenSpec TUI Editor Application."""
    
    CSS = """
    Screen {
        background: $background;
    }
    """
    
    TITLE = "OpenSpec TUI Editor"
    SUB_TITLE = "Spec-driven development for AI"
    
    def on_mount(self):
        """Initialize the application."""
        self.push_screen(MainScreen())


def main():
    """Entry point for the console script."""
    app = OpenSpecTUI()
    app.run()


if __name__ == "__main__":
    main()
