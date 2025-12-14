# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[('templates', 'templates'), ('validators', 'validators')],
    hiddenimports=['validators.run_all', 'validators.base_validator', 'validators.v01_page_setup', 'validators.v02_cover', 'validators.v03_abstract_cn', 'validators.v04_keywords_cn', 'validators.v05_abstract_en', 'validators.v06_keywords_en', 'validators.v07_toc', 'validators.v08_heading1', 'validators.v09_heading2', 'validators.v10_heading3', 'validators.v11_paragraph', 'validators.v12_word_count', 'validators.v13_figure', 'validators.v14_table', 'validators.v14b_table_continuation', 'validators.v15_three_line_table', 'validators.v16_formula', 'validators.v17_footnote', 'validators.v18_reference_title', 'validators.v19_reference_content', 'validators.v20_citation', 'validators.v21_punctuation', 'validators.v22_number', 'validators.v23_china_region', 'validators.v24_header', 'validators.v25_footer', 'validators.v26_appendix', 'validators.v27_acknowledgement', 'validators.v28_resume', 'validators.v29_spine', 'validators.v30_structure'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ThesisValidator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
app = BUNDLE(
    exe,
    name='ThesisValidator.app',
    icon=None,
    bundle_identifier=None,
)
