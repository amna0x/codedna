import { inject, injectable } from '@theia/core/shared/inversify';
import { FrontendApplicationContribution } from '@theia/core/lib/browser';
import { ThemeService } from '@theia/core/lib/browser/theming';
import { MonacoThemingService } from '@theia/monaco/lib/browser/monaco-theming-service';

export const CODEDNA_THEME_ID = 'codedna-dark';

/**
 * CodeDNA Dark: deep "void" background, translucent glass surfaces, teal →
 * indigo accent. Sibling of FreshOptimizer's design language, with its own
 * accent. Surfaces are semi-transparent so the shell wallpaper
 * (style/codedna-shell.css) shows through, like frosted glass.
 */
const COLORS: Record<string, string> = {
    'foreground': '#E6E8EE',
    'descriptionForeground': '#8F94A6',
    'focusBorder': '#2DD4BF80',
    'widget.border': '#FFFFFF10',
    'widget.shadow': '#00000080',
    'selection.background': '#2DD4BF40',
    'icon.foreground': '#C9CEDA',

    'editor.background': '#0C0F15D9',
    'editor.foreground': '#E6E8EE',
    'editorLineNumber.foreground': '#454C5E',
    'editorLineNumber.activeForeground': '#C9CEDA',
    'editor.lineHighlightBackground': '#FFFFFF07',
    'editor.lineHighlightBorder': '#00000000',
    'editor.selectionBackground': '#2DD4BF33',
    'editor.inactiveSelectionBackground': '#2DD4BF1A',
    'editor.findMatchBackground': '#6366F166',
    'editor.findMatchHighlightBackground': '#6366F133',
    'editorCursor.foreground': '#5EEAD4',
    'editorIndentGuide.background1': '#FFFFFF0A',
    'editorIndentGuide.activeBackground1': '#FFFFFF24',
    'editorWhitespace.foreground': '#FFFFFF12',
    'editorGutter.background': '#00000000',
    'editorWidget.background': '#151922F2',
    'editorWidget.border': '#FFFFFF14',
    'editorHoverWidget.background': '#151922F2',
    'editorHoverWidget.border': '#FFFFFF14',
    'editorSuggestWidget.background': '#151922F2',
    'editorSuggestWidget.border': '#FFFFFF14',
    'editorSuggestWidget.selectedBackground': '#2DD4BF26',
    'editorWarning.foreground': '#FFB020',
    'editorError.foreground': '#FF5C6C',
    'editorInfo.foreground': '#67E8F9',
    'minimap.background': '#00000000',

    'sideBar.background': '#12151CB8',
    'sideBar.foreground': '#C9CEDA',
    'sideBar.border': '#00000000',
    'sideBarTitle.foreground': '#8F94A6',
    'sideBarSectionHeader.background': '#00000000',
    'sideBarSectionHeader.foreground': '#8F94A6',
    'sideBarSectionHeader.border': '#FFFFFF0A',

    'activityBar.background': '#00000000',
    'activityBar.foreground': '#E6E8EE',
    'activityBar.inactiveForeground': '#6B7183',
    'activityBar.activeBorder': '#2DD4BF',
    'activityBar.border': '#00000000',
    'activityBarBadge.background': '#2DD4BF',
    'activityBarBadge.foreground': '#04120F',

    'titleBar.activeBackground': '#00000000',
    'titleBar.inactiveBackground': '#00000000',
    'titleBar.activeForeground': '#C9CEDA',
    'titleBar.inactiveForeground': '#6B7183',
    'titleBar.border': '#00000000',
    'menubar.selectionBackground': '#FFFFFF10',
    'menubar.selectionForeground': '#E6E8EE',
    'menu.background': '#151922F5',
    'menu.foreground': '#E6E8EE',
    'menu.border': '#FFFFFF14',
    'menu.selectionBackground': '#2DD4BF26',
    'menu.selectionForeground': '#E6E8EE',
    'menu.separatorBackground': '#FFFFFF10',

    'tab.activeBackground': '#FFFFFF10',
    'tab.unfocusedActiveBackground': '#FFFFFF0A',
    'tab.inactiveBackground': '#00000000',
    'tab.activeForeground': '#E6E8EE',
    'tab.inactiveForeground': '#8F94A6',
    'tab.hoverBackground': '#FFFFFF08',
    'tab.border': '#00000000',
    'tab.activeBorder': '#00000000',
    'tab.activeBorderTop': '#00000000',
    'tab.unfocusedActiveBorderTop': '#00000000',
    'editorGroupHeader.tabsBackground': '#00000000',
    'editorGroupHeader.tabsBorder': '#00000000',
    'editorGroup.border': '#FFFFFF0A',
    'breadcrumb.background': '#00000000',
    'breadcrumb.foreground': '#8F94A6',

    'panel.background': '#12151CB8',
    'panel.border': '#00000000',
    'panelTitle.activeForeground': '#E6E8EE',
    'panelTitle.inactiveForeground': '#8F94A6',
    'panelTitle.activeBorder': '#2DD4BF',

    'statusBar.background': '#00000000',
    'statusBar.foreground': '#8F94A6',
    'statusBar.border': '#00000000',
    'statusBar.noFolderBackground': '#00000000',
    'statusBar.debuggingBackground': '#6366F1',
    'statusBarItem.hoverBackground': '#FFFFFF10',
    'statusBarItem.remoteBackground': '#00000000',

    'list.hoverBackground': '#FFFFFF0A',
    'list.activeSelectionBackground': '#2DD4BF26',
    'list.activeSelectionForeground': '#E6E8EE',
    'list.inactiveSelectionBackground': '#FFFFFF0D',
    'list.focusOutline': '#2DD4BF66',
    'list.highlightForeground': '#5EEAD4',
    'tree.indentGuidesStroke': '#FFFFFF14',

    'input.background': '#00000040',
    'input.border': '#FFFFFF14',
    'input.foreground': '#E6E8EE',
    'input.placeholderForeground': '#6B7183',
    'inputOption.activeBorder': '#2DD4BF',
    'inputValidation.errorBackground': '#FF5C6C1A',
    'inputValidation.errorBorder': '#FF5C6C66',
    'inputValidation.warningBackground': '#FFB0201A',
    'inputValidation.warningBorder': '#FFB02066',
    'dropdown.background': '#151922',
    'dropdown.border': '#FFFFFF14',
    'dropdown.foreground': '#E6E8EE',
    'checkbox.background': '#00000040',
    'checkbox.border': '#FFFFFF24',

    'button.background': '#2DD4BF',
    'button.foreground': '#04120F',
    'button.hoverBackground': '#5EEAD4',
    'button.secondaryBackground': '#FFFFFF10',
    'button.secondaryForeground': '#E6E8EE',
    'button.secondaryHoverBackground': '#FFFFFF1A',

    'quickInput.background': '#151922F5',
    'quickInputList.focusBackground': '#2DD4BF26',
    'pickerGroup.foreground': '#5EEAD4',
    'pickerGroup.border': '#FFFFFF14',
    'notifications.background': '#151922F5',
    'notifications.border': '#FFFFFF14',
    'notificationCenterHeader.background': '#1A1F29',

    'scrollbar.shadow': '#00000000',
    'scrollbarSlider.background': '#FFFFFF14',
    'scrollbarSlider.hoverBackground': '#2DD4BF59',
    'scrollbarSlider.activeBackground': '#2DD4BF80',

    'terminal.background': '#00000000',
    'terminal.foreground': '#C9CEDA',
    'terminalCursor.foreground': '#5EEAD4',

    'gitDecoration.addedResourceForeground': '#34D399',
    'gitDecoration.untrackedResourceForeground': '#34D399',
    'gitDecoration.modifiedResourceForeground': '#FFB020',
    'gitDecoration.deletedResourceForeground': '#FF5C6C',

    'badge.background': '#2DD4BF33',
    'badge.foreground': '#5EEAD4',
    'progressBar.background': '#2DD4BF',
    'textLink.foreground': '#5EEAD4',
    'textLink.activeForeground': '#99F6E4',
    'textCodeBlock.background': '#FFFFFF0D',
    'textPreformat.foreground': '#99F6E4',
    'welcomePage.tileBackground': '#12151CB8'
};

const TOKEN_COLORS = [
    { scope: ['comment', 'punctuation.definition.comment'], settings: { foreground: '#5C6478', fontStyle: 'italic' } },
    { scope: ['keyword', 'storage.type', 'storage.modifier'], settings: { foreground: '#8B9CFF' } },
    { scope: ['string', 'string.quoted'], settings: { foreground: '#7EE7C7' } },
    { scope: ['constant.numeric', 'constant.language'], settings: { foreground: '#FFB86B' } },
    { scope: ['entity.name.type', 'entity.name.class', 'support.type', 'support.class'], settings: { foreground: '#67E8F9' } },
    { scope: ['entity.name.function', 'support.function', 'meta.method-call'], settings: { foreground: '#A5B4FC' } },
    { scope: ['variable.parameter'], settings: { foreground: '#E6E8EE', fontStyle: 'italic' } },
    { scope: ['variable', 'meta.definition.variable'], settings: { foreground: '#E6E8EE' } },
    { scope: ['storage.type.annotation', 'meta.annotation', 'punctuation.definition.annotation'], settings: { foreground: '#F0ABFC' } },
    { scope: ['punctuation', 'meta.brace'], settings: { foreground: '#9AA1B2' } },
    { scope: ['invalid'], settings: { foreground: '#FF5C6C' } }
];

@injectable()
export class CodeDnaThemeContribution implements FrontendApplicationContribution {

    @inject(MonacoThemingService) protected readonly theming: MonacoThemingService;
    @inject(ThemeService) protected readonly themes: ThemeService;

    initialize(): void {
        this.theming.registerParsedTheme({
            id: CODEDNA_THEME_ID,
            label: 'CodeDNA Dark',
            uiTheme: 'vs-dark',
            description: 'Glass surfaces on a deep background with a teal accent.',
            json: { type: 'dark', colors: COLORS, tokenColors: TOKEN_COLORS }
        });
        // The glass shell styles (codedna-shell.css) apply only with this theme,
        // so other themes keep Theia's normal, opaque layout.
        const sync = () => document.body.classList.toggle(
            'codedna-shell', this.themes.getCurrentTheme().id === CODEDNA_THEME_ID);
        this.themes.onDidColorThemeChange(sync);
        sync();
    }
}
