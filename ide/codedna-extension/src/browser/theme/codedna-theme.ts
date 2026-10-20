import { inject, injectable } from '@theia/core/shared/inversify';
import { FrontendApplicationContribution } from '@theia/core/lib/browser';
import { ThemeService } from '@theia/core/lib/browser/theming';
import { MonacoThemingService } from '@theia/monaco/lib/browser/monaco-theming-service';

export const CODEDNA_THEME_ID = 'codedna-dark';

/**
 * CodeDNA Dark (D-031): neutral graphite surfaces, warm off-white text, no
 * accent hue. Colour is reserved for meaning — new (green), changed (amber),
 * removed / error (red) — so nothing on screen competes with the code or with
 * those signals. No glows, gradients or translucency.
 */
const C = {
    canvas: '#0C0C0D',     // gaps between panels
    surface: '#151516',    // side panels
    editor: '#121213',     // main stage
    raised: '#1C1C1E',     // menus, popovers, inputs
    line: '#FFFFFF12',
    lineSoft: '#FFFFFF0A',
    text: '#ECECE8',
    muted: '#9C9C96',
    faint: '#66665F',
    ink: '#111112',        // text on the light primary button
    green: '#86B38A',
    amber: '#D8A657',
    red: '#D8675F',
    selection: '#ECECE826'
};

const COLORS: Record<string, string> = {
    'foreground': C.text,
    'descriptionForeground': C.muted,
    'focusBorder': '#ECECE880',
    'widget.border': C.line,
    'widget.shadow': '#00000066',
    'selection.background': C.selection,
    'icon.foreground': '#C8C8C2',

    'editor.background': C.editor,
    'editor.foreground': C.text,
    'editorLineNumber.foreground': '#4A4A46',
    'editorLineNumber.activeForeground': '#C8C8C2',
    'editor.lineHighlightBackground': '#FFFFFF06',
    'editor.lineHighlightBorder': '#00000000',
    'editor.selectionBackground': '#ECECE829',
    'editor.inactiveSelectionBackground': '#ECECE814',
    'editor.findMatchBackground': '#D8A65766',
    'editor.findMatchHighlightBackground': '#D8A65730',
    'editorCursor.foreground': C.text,
    'editorIndentGuide.background1': '#FFFFFF0A',
    'editorIndentGuide.activeBackground1': '#FFFFFF22',
    'editorWhitespace.foreground': '#FFFFFF10',
    'editorWidget.background': C.raised,
    'editorWidget.border': C.line,
    'editorHoverWidget.background': C.raised,
    'editorHoverWidget.border': C.line,
    'editorSuggestWidget.background': C.raised,
    'editorSuggestWidget.border': C.line,
    'editorSuggestWidget.selectedBackground': '#FFFFFF14',
    'editorWarning.foreground': C.amber,
    'editorError.foreground': C.red,
    'editorInfo.foreground': '#B9B9B2',
    'minimap.background': C.editor,

    'sideBar.background': C.surface,
    'sideBar.foreground': '#D6D6D0',
    'sideBar.border': '#00000000',
    'sideBarTitle.foreground': C.muted,
    'sideBarSectionHeader.background': '#00000000',
    'sideBarSectionHeader.foreground': C.muted,
    'sideBarSectionHeader.border': C.lineSoft,

    'activityBar.background': C.canvas,
    'activityBar.foreground': C.text,
    'activityBar.inactiveForeground': C.faint,
    'activityBar.activeBorder': C.text,
    'activityBar.border': '#00000000',
    'activityBarBadge.background': C.text,
    'activityBarBadge.foreground': C.ink,

    'titleBar.activeBackground': C.canvas,
    'titleBar.inactiveBackground': C.canvas,
    'titleBar.activeForeground': '#C8C8C2',
    'titleBar.inactiveForeground': C.faint,
    'titleBar.border': '#00000000',
    'menubar.selectionBackground': '#FFFFFF10',
    'menubar.selectionForeground': C.text,
    'menu.background': C.raised,
    'menu.foreground': C.text,
    'menu.border': C.line,
    'menu.selectionBackground': '#FFFFFF14',
    'menu.selectionForeground': C.text,
    'menu.separatorBackground': C.line,

    'tab.activeBackground': C.editor,
    'tab.unfocusedActiveBackground': C.editor,
    'tab.inactiveBackground': '#00000000',
    'tab.activeForeground': C.text,
    'tab.inactiveForeground': C.muted,
    'tab.hoverBackground': '#FFFFFF08',
    'tab.border': '#00000000',
    'tab.activeBorder': '#00000000',
    'tab.activeBorderTop': '#00000000',
    'tab.unfocusedActiveBorderTop': '#00000000',
    'editorGroupHeader.tabsBackground': C.surface,
    'editorGroupHeader.tabsBorder': '#00000000',
    'editorGroup.border': C.lineSoft,
    'breadcrumb.background': C.editor,
    'breadcrumb.foreground': C.muted,

    'panel.background': C.surface,
    'panel.border': '#00000000',
    'panelTitle.activeForeground': C.text,
    'panelTitle.inactiveForeground': C.muted,
    'panelTitle.activeBorder': C.text,

    'statusBar.background': C.canvas,
    'statusBar.foreground': C.muted,
    'statusBar.border': '#00000000',
    'statusBar.noFolderBackground': C.canvas,
    'statusBar.debuggingBackground': '#3A3A36',
    'statusBarItem.hoverBackground': '#FFFFFF10',
    'statusBarItem.remoteBackground': C.canvas,

    'list.hoverBackground': '#FFFFFF08',
    'list.activeSelectionBackground': '#FFFFFF14',
    'list.activeSelectionForeground': C.text,
    'list.inactiveSelectionBackground': '#FFFFFF0C',
    'list.focusOutline': '#ECECE866',
    'list.highlightForeground': C.text,
    'tree.indentGuidesStroke': '#FFFFFF12',

    'input.background': C.raised,
    'input.border': C.line,
    'input.foreground': C.text,
    'input.placeholderForeground': C.faint,
    'inputOption.activeBorder': '#ECECE899',
    'inputValidation.errorBackground': '#D8675F1A',
    'inputValidation.errorBorder': '#D8675F66',
    'inputValidation.warningBackground': '#D8A6571A',
    'inputValidation.warningBorder': '#D8A65766',
    'dropdown.background': C.raised,
    'dropdown.border': C.line,
    'dropdown.foreground': C.text,
    'checkbox.background': C.raised,
    'checkbox.border': '#FFFFFF24',

    'button.background': C.text,
    'button.foreground': C.ink,
    'button.hoverBackground': '#FFFFFF',
    'button.secondaryBackground': '#FFFFFF10',
    'button.secondaryForeground': C.text,
    'button.secondaryHoverBackground': '#FFFFFF1A',

    'quickInput.background': C.raised,
    'quickInputList.focusBackground': '#FFFFFF14',
    'pickerGroup.foreground': C.muted,
    'pickerGroup.border': C.line,
    'notifications.background': C.raised,
    'notifications.border': C.line,
    'notificationCenterHeader.background': '#202022',

    'scrollbar.shadow': '#00000000',
    'scrollbarSlider.background': '#FFFFFF12',
    'scrollbarSlider.hoverBackground': '#FFFFFF24',
    'scrollbarSlider.activeBackground': '#FFFFFF33',

    'terminal.background': C.surface,
    'terminal.foreground': '#D6D6D0',
    'terminalCursor.foreground': C.text,

    'gitDecoration.addedResourceForeground': C.green,
    'gitDecoration.untrackedResourceForeground': C.green,
    'gitDecoration.modifiedResourceForeground': C.amber,
    'gitDecoration.deletedResourceForeground': C.red,

    'badge.background': '#FFFFFF1A',
    'badge.foreground': C.text,
    'progressBar.background': C.text,
    'textLink.foreground': C.text,
    'textLink.activeForeground': '#FFFFFF',
    'textCodeBlock.background': '#FFFFFF0D',
    'textPreformat.foreground': '#D6D6D0',
    'welcomePage.tileBackground': C.surface
};

/** Muted, warm syntax colours: readable for hours, nothing neon. */
const TOKEN_COLORS = [
    { scope: ['comment', 'punctuation.definition.comment'], settings: { foreground: '#6E6E67', fontStyle: 'italic' } },
    { scope: ['keyword', 'storage.type', 'storage.modifier'], settings: { foreground: '#CF8E6D' } },
    { scope: ['string', 'string.quoted'], settings: { foreground: '#A9C08F' } },
    { scope: ['constant.numeric', 'constant.language'], settings: { foreground: '#D7B46A' } },
    { scope: ['entity.name.type', 'entity.name.class', 'support.type', 'support.class'], settings: { foreground: '#D9C9A3' } },
    { scope: ['entity.name.function', 'support.function', 'meta.method-call'], settings: { foreground: '#E6E1D6' } },
    { scope: ['variable.parameter'], settings: { foreground: '#ECECE8', fontStyle: 'italic' } },
    { scope: ['variable', 'meta.definition.variable'], settings: { foreground: '#ECECE8' } },
    { scope: ['storage.type.annotation', 'meta.annotation', 'punctuation.definition.annotation'], settings: { foreground: '#BFA6A0' } },
    { scope: ['entity.name.tag'], settings: { foreground: '#CF8E6D' } },
    { scope: ['entity.other.attribute-name'], settings: { foreground: '#D9C9A3' } },
    { scope: ['punctuation', 'meta.brace'], settings: { foreground: '#8E8E87' } },
    { scope: ['invalid'], settings: { foreground: '#D8675F' } }
];

@injectable()
export class CodeDnaThemeContribution implements FrontendApplicationContribution {

    @inject(MonacoThemingService) protected readonly theming: MonacoThemingService;
    @inject(ThemeService) protected readonly themes: ThemeService;

    initialize(): void {
        this.register();
        // The shell styles (codedna-shell.css) apply only with this theme, so
        // other themes keep Theia's normal layout.
        const sync = () => document.body.classList.toggle(
            'codedna-shell', this.themes.getCurrentTheme().id === CODEDNA_THEME_ID);
        this.themes.onDidColorThemeChange(sync);
        sync();
    }

    /**
     * Theia restores parsed themes from an IndexedDB cache asynchronously at
     * start-up, which would bring back an older version of this theme after an
     * update. Registering again once the app has started wins over the cache
     * and refreshes it.
     */
    onStart(): void {
        this.register();
    }

    protected register(): void {
        this.theming.registerParsedTheme({
            id: CODEDNA_THEME_ID,
            label: 'CodeDNA Dark',
            uiTheme: 'vs-dark',
            description: 'Calm graphite surfaces; colour only where it carries meaning.',
            json: { type: 'dark', colors: COLORS, tokenColors: TOKEN_COLORS }
        });
    }
}
