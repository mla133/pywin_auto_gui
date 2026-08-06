# Regression Coverage Status

A living status matrix mapping every scenario ID in `scenarios/regression.md`
to its automation state in `tests/`. Regenerate/update this whenever a
scenario's status changes (e.g. a `manual`/`special_case`/
`needs_live_verification` marker is added or removed).

**Drift guard**: `tests/test_regression_coverage_doc.py` runs as part of
the default suite (no live app/device needed) and fails the build if this
doc ever falls out of sync — it checks that every `scenarios/regression.md`
scenario ID has a row here (and vice versa), and that every `test_...`
reference in the Test column still resolves to a real, existing test
function. It won't catch every kind of drift (e.g. a Status column that no
longer matches a test's actual markers), but it does guarantee the ID
list and test references stay accurate.

**Legend:**

- ✅ **Automated** — live-verified passing, runs as part of the default `pytest -s -v` suite.
- 🔧 **Automated (marked)** — automated but excluded from the default suite by a marker (`requires_device`, `disruptive`, `installs_software`, `needs_live_verification` pending live verification) — see [`running-tests.md`](running-tests.md) for how to run these explicitly.
- 🙋 **Manual** (`@pytest.mark.manual`) — cannot be automated from this repo at all; must be performed by a human tester.
- 🧩 **Special case** (`@pytest.mark.special_case`) — automatable in principle, but only applies to a device state this repo can't safely arrange/verify (e.g. "no file present" after a Factory Init); intentionally excluded from the standard pass.
- 🚫 **Out of scope** — deliberately not attempted (documented reasoning below).

## Section A — Config Files, Device Connectivity, Terminal, Print/General Options

| ID  | Title                                    | Status                               | Test                                                                                  |
| --- | ---------------------------------------- | ------------------------------------ | ------------------------------------------------------------------------------------- |
| A1  | Creating New Config Files                | ✅                                    | `test_regression_config_files.py::test_a1_creating_new_config_file`                   |
| A2  | Saving Config Files                      | ✅                                    | `test_a2_saving_config_file`                                                          |
| A3  | Loading Current AL4 Config Files         | 🔧 requires `--accumate-config-file` | `test_a3_loading_current_al4_config_file`                                             |
| A4  | Loading Old AL4 Config Files             | ✅                                    | `test_a4_loading_old_al4_config_files`                                                |
| A5  | Loading A3X Config Files                 | ✅                                    | `test_a5_loading_a3x_config_files`                                                    |
| A6  | Conversion Of Old AccuMate 4 Offsets     | ✅                                    | `test_a6_conversion_of_old_al4_offsets`                                               |
| A7  | Manually Connecting to an AccuLoad       | 🔧 `requires_device`                 | `test_regression_device_web.py::test_a7_manually_connecting_to_accuload`              |
| A8  | Automatically Connecting to an AccuLoad  | 🔧 `requires_device`                 | `test_a8_automatically_connecting_to_accuload`                                        |
| A9  | Valid Arm Addresses                      | 🔧 `requires_device`                 | `test_a9_valid_arm_addresses`                                                         |
| A10 | Pushing Full Configurations              | 🔧 `requires_device`, `disruptive`   | `test_a10_pushing_full_configuration`                                                 |
| A11 | Pulling Full Configurations              | 🔧 `requires_device`                 | `test_a11_pulling_full_configuration`                                                 |
| A12 | Pushing Selected Configurations          | 🔧 `requires_device`                 | `test_a12_pushing_selected_configuration`                                             |
| A13 | Pulling Selected Configurations          | 🔧 `requires_device`                 | `test_a13_pulling_selected_configuration`                                             |
| A14 | Downloading Totalizers                   | 🔧 `requires_device`                 | `test_a14_downloading_totalizers`                                                     |
| A15 | Changing Values in a Config              | ✅                                    | `test_regression_config_files.py::test_a15_changing_values_in_config`                 |
| A16 | Calling Help                             | ✅                                    | `test_regression_help.py::test_a16_calling_help`                                      |
| A17 | Calling Context Help                     | ✅                                    | `test_a17_calling_context_help`                                                       |
| A18 | Smithcomm "HI"                           | 🔧 `requires_device`                 | `test_regression_device.py::test_a18_terminal_emulator_hi_command`                    |
| A19 | Terminal PUSH Command                    | 🔧 `requires_device`, `disruptive`   | `test_a19_terminal_push_command`                                                      |
| A20 | Terminal PULL Command                    | 🔧 `requires_device`                 | `test_a20_terminal_pull_command`                                                      |
| A21 | Going Offline                            | 🔧 `requires_device`                 | `test_a21_going_offline`                                                              |
| A22 | Retrying Communication                   | 🔧 `requires_device`                 | `test_a22_retrying_communication`                                                     |
| A23 | General Options - Print Security Level   | ✅                                    | `test_regression_print.py::test_a23_print_security_level`                             |
| A24 | General Options - Display Security Level | ✅                                    | `test_regression_general_options.py::test_a24_general_options_display_security_level` |
| A25 | General Options - Print Unused Recipes   | ✅                                    | `test_regression_print.py::test_a25_print_unused_recipes`                             |
| A26 | General Options - Limit Printout         | ✅                                    | `test_a26_limit_printout`                                                             |
| A27 | Document Options - Default IP            | ✅                                    | `test_regression_general_options.py::test_a27_document_options_default_ip`            |

## Section B — Report Editor

| ID  | Title                                         | Status                                          | Test                                                                  |
| --- | --------------------------------------------- | ----------------------------------------------- | --------------------------------------------------------------------- |
| B1  | Creating New Report Files                     | ✅                                               | `test_regression_b.py::test_b1_creating_new_report_files`             |
| B2  | Saving Report Files                           | ✅                                               | `test_b2_saving_report_files`                                         |
| B3  | Loading Report Files                          | ✅                                               | `test_b3_loading_report_files`                                        |
| B4  | Uploading Empty Report File                   | 🔧 `requires_device`, `needs_live_verification` | `test_b4_uploading_empty_report_file`                                 |
| B5  | Uploading Report Files - Transaction Report   | 🔧                                              | `test_b5_uploading_report_files_transaction_report`                   |
| B6  | Downloading Report Files - Transaction Report | 🔧                                              | `test_b6_downloading_report_files_transaction_report`                 |
| B7  | Uploading Report Files - Batch Report         | 🔧                                              | `test_b7_uploading_report_files_batch_report`                         |
| B8  | Downloading Report Files - Batch Report       | 🔧                                              | `test_b8_downloading_report_files_batch_report`                       |
| B9  | Uploading Report Files - Prove Report         | 🔧                                              | `test_b9_uploading_report_files_prove_report`                         |
| B10 | Downloading Report Files - Prove Report       | 🔧                                              | `test_b10_downloading_report_files_prove_report`                      |
| B11 | Loading AM3 Report Files                      | ✅                                               | `test_b11_loading_am3_report_files` (uses `configs/B11.RPX`)          |
| B12 | Loading Early AM4 Report Files                | ✅                                               | `test_b12_loading_early_am4_report_files` (uses `configs/B12.al4rep`) |
| B13 | Upload/Download Multiple Times                | 🔧                                              | `test_b13_upload_download_multiple_times`                             |
| B14 | No Report To Download                         | 🧩 special case                                 | `test_b14_no_report_to_download`                                      |
| B15 | Creating UserText Items                       | ✅                                               | `test_b15_creating_usertext_items`                                    |
| B16 | Creating Value/Description Items              | ✅                                               | `test_b16_creating_value_description_items`                           |
| B17 | Creating Value/Description Items with Offsets | ✅                                               | `test_b17_creating_value_description_items_with_offsets`              |
| B18 | Changing the Format of Report Items           | ✅                                               | `test_b18_changing_the_format_of_report_items`                        |
| B19 | Using Invalid Formats for String Report Items | ✅                                               | `test_b19_using_invalid_formats_for_string_report_items`              |
| B20 | Moving Items                                  | ✅                                               | `test_b20_moving_items`                                               |
| B21 | Moving Items over other Items                 | ✅                                               | `test_b21_moving_items_over_other_items`                              |
| B22 | Copy/Paste Items                              | ✅                                               | `test_b22_copy_paste_items`                                           |
| B23 | Copy/Paste Text as an Item                    | ✅                                               | `test_b23_copy_paste_text_as_an_item`                                 |
| B24 | Creating Items Out of Bounds                  | ✅                                               | `test_b24_creating_items_out_of_bounds`                               |
| B25 | Moving Items Out of Bounds                    | ✅                                               | `test_b25_moving_items_out_of_bounds`                                 |
| B26 | Changing Document Size                        | ✅                                               | `test_b26_changing_document_size`                                     |
| B27 | Changing Document Size - Items Out of Bounds  | ✅                                               | `test_b27_changing_document_size_items_out_of_bounds`                 |
| B28 | Changing Number of Pages in a Document        | ✅                                               | `test_b28_changing_number_of_pages_in_a_document`                     |

## Section C — Translation Editor

| ID  | Title                           | Status               | Test                                                            |
| --- | ------------------------------- | -------------------- | --------------------------------------------------------------- |
| C1  | Creating New Translation Files  | ✅                    | `test_regression_c.py::test_c1_creating_new_translation_files`  |
| C2  | Saving Translation Files        | ✅                    | `test_c2_saving_translation_files`                              |
| C3  | Loading Translation Files       | ✅                    | `test_c3_loading_translation_files`                             |
| C4  | Uploading Translation Files     | 🔧 `requires_device` | `test_c4_uploading_translation_files`                           |
| C5  | Downloading Translation Files   | 🔧 `requires_device` | `test_c5_downloading_translation_files`                         |
| C6  | No Translation File To Download | 🧩 special case      | `test_c6_no_translation_file_to_download`                       |
| C7  | Loading AM3 Translation Files   | ✅                    | `test_c7_loading_am3_translation_files` (uses `configs/C7.LGX`) |

## Section D — Driver Database

| ID  | Title                               | Status               | Test                                                                |
| --- | ----------------------------------- | -------------------- | ------------------------------------------------------------------- |
| D1  | Create New Driver Database Files    | ✅                    | `test_regression_d.py::test_d1_create_new_driver_database_file`     |
| D2  | Creating Driver Database Entries    | ✅                    | `test_d2_creating_driver_database_entries`                          |
| D3  | Editing a Driver Database Entry     | ✅                    | `test_d3_editing_a_driver_database_entry`                           |
| D4  | Saving Driver Database Files        | ✅                    | `test_d4_saving_driver_database_files`                              |
| D5  | Loading Driver Database Files       | ✅                    | `test_d5_loading_driver_database_files`                             |
| D6  | Uploading Driver Database Files     | 🔧 `requires_device` | `test_d6_uploading_driver_database_files`                           |
| D7  | Downloading Driver Database Files   | 🔧 `requires_device` | `test_d7_downloading_driver_database_files`                         |
| D8  | No Driver Database File To Download | 🧩 special case      | `test_d8_no_driver_database_file_to_download`                       |
| D9  | Loading AM3 Driver Database Files   | ✅                    | `test_d9_loading_am3_driver_database_files` (uses `configs/D9.3DB`) |

## Section E — Equation Editor

| ID  | Title                         | Status               | Test                                                         |
| --- | ----------------------------- | -------------------- | ------------------------------------------------------------ |
| E1  | Create New Equation Files     | ✅                    | `test_regression_e.py::test_e1_create_new_equation_file`     |
| E2  | Saving Equation Files         | ✅                    | `test_e2_saving_equation_files`                              |
| E3  | Loading Equation Files        | ✅                    | `test_e3_loading_equation_files`                             |
| E4  | Uploading Equation Files      | 🔧 `requires_device` | `test_e4_uploading_equation_files`                           |
| E5  | Downloading Equation Files    | 🔧 `requires_device` | `test_e5_downloading_equation_files`                         |
| E6  | No Equation File To Download  | 🧩 special case      | `test_e6_no_equation_file_to_download`                       |
| E7  | Loading AM3 Equation Files    | ✅                    | `test_e7_loading_am3_equation_files` (uses `configs/E7.EQX`) |
| E8  | Uploading Empty Equation File | 🔧 `requires_device` | `test_e8_uploading_empty_equation_file`                      |

## Section F — Logs, License Status, Firmware, Printing, A3X Conversions

| ID  | Title                                               | Status               | Test                                                                                               |
| --- | --------------------------------------------------- | -------------------- | -------------------------------------------------------------------------------------------------- |
| F1  | Downloading Empty Transaction Log                   | 🔧 `requires_device` | `test_regression_f.py::test_f1_downloading_empty_transaction_log`                                  |
| F2  | Download Transaction Log (Small)                    | 🔧                   | `test_f2_download_transaction_log_small`                                                           |
| F3  | Download Transaction Log (Large)                    | 🔧                   | `test_f3_download_transaction_log_large`                                                           |
| F4  | Download Event Log                                  | 🔧                   | `test_f4_download_event_log`                                                                       |
| F5  | Download Audit Trail Log                            | 🔧                   | `test_f5_download_audit_trail_log`                                                                 |
| F6  | Upload/Download License Status File                 | 🙋 **manual**        | `test_f6_upload_download_license_status_file` — needs a real License Status file, not supplied     |
| F7  | No License Status To Download                       | 🔧 `requires_device` | `test_f7_no_license_status_to_download`                                                            |
| F8  | Update AccuLoad Firmware                            | 🙋 **manual**        | `test_f8_update_accuload_firmware` — needs a firmware file + an unbuilt "Firmware Update" workflow |
| F9  | Printing DriverDB Files (One Page)                  | ✅                    | `test_f9_printing_driverdb_files_one_page`                                                         |
| F10 | Printing DriverDB Files (Multiple Pages)            | ✅                    | `test_f10_printing_driverdb_files_multiple_pages`                                                  |
| F11 | Printing AccuMate Config Files                      | ✅                    | `test_f11_printing_accumate_config_files`                                                          |
| F12 | Printing Equation Files (Multiple Pages)            | ✅                    | `test_f12_printing_equation_files_multiple_pages`                                                  |
| F13 | Printing Equation Files (One Page)                  | ✅                    | `test_f13_printing_equation_files_one_page`                                                        |
| F14 | API Table Conversions From A3X to AL4               | ✅                    | `test_f14_api_table_conversions_from_a3x_to_al4` (uses `configs/F14.A3X`)                          |
| F15 | Parameter Conversions from A3X - Configuration File | ✅                    | `test_f15_parameter_conversions_from_a3x_configuration_file` (uses `configs/F15.A3X`)              |
| F16 | Parameter Conversions from A3X - Report File        | ✅                    | `test_f16_parameter_conversions_from_a3x_report_file` (uses `configs/F16.RPX`)                     |
| F17 | Parameter Conversions from A3X - Equations File     | ✅                    | `test_f17_parameter_conversions_from_a3x_equations_file` (uses `configs/F17.EQX`)                  |

## Section G — Installer

| ID                           | Title                                                               | Status                 | Test                                                                                                                                                                                                                          |
| ---------------------------- | ------------------------------------------------------------------- | ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| G1                           | Installing new version can't create new config docs (while running) | 🔧 `installs_software` | `test_regression_g.py::test_g1_block_reinstall_while_app_running`, `test_g1_new_config_after_install`                                                                                                                         |
| G1 (uninstall-while-running) | —                                                                   | 🙋 **manual**          | `test_g1_block_uninstall_while_app_running` — needs a live human check of whether `AccuMate.exe` registers Inno's AppMutex, or access to the AccuMate C++/MFC source                                                          |
| G2                           | Terms & Conditions in the Installer                                 | ✅                      | `test_g2_license_agreement_shown_before_install`                                                                                                                                                                              |
| G3                           | Install AccuMate as normal user                                     | 🔧 `installs_software` | `test_g3_install_as_normal_user`, `test_g3_about_version_after_install`, `test_g3_start_menu_shortcut_created`, `test_g3_desktop_icon_start_not_applicable`, `test_g3_al4_file_association_double_click`, `test_g3_uninstall` |
| G4                           | Install AccuMate as Admin for All Users                             | 🙋 **manual**          | `test_g4_install_as_admin_all_users` — needs an elevated (Administrator) session, never yet probed                                                                                                                            |
| G5                           | Install AccuMate as Admin for the Current User                      | 🙋 **manual**          | `test_g5_install_as_admin_current_user` — same blocker as G4                                                                                                                                                                  |

## Section H — Help Content / Parameter Regressions

| ID    | Title                                                         | Status              | Test                                                                                                                                                                                                         |
| ----- | ------------------------------------------------------------- | ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| H1    | DY Help file matches Smith Manual (injectors 1-44)            | ✅                   | `test_regression_h.py::test_h1_dy_help_shows_injectors_1_to_44`                                                                                                                                              |
| H2    | EA Help file / 2-char codes match Smith Manual                | ✅                   | `test_h2_ea_help_shows_injectors_25_to_44`                                                                                                                                                                   |
| H3-H8 | Updated max values for Parameters                             | 🚫 **out of scope** | Needs PuTTY access to the AccuLoad's `/dev/shm`, live batch runs, and PDF report comparisons — deliberately not attempted by this app-only automation approach (see `test_regression_h.py` module docstring) |
| H9    | HMI B Failure parameter removed from System Directory Listing | ✅                   | `test_h9_hmi_b_failure_parameter_removed`                                                                                                                                                                    |

## Summary

- **106** total scenario IDs (or ID groups) in `scenarios/regression.md`.
- **~57** automated and passing in the default suite (✅).
- **~40** automated but require an explicit marker override to run (🔧) —
  mostly `requires_device`, since a live AccuLoad isn't always reachable.
- **5** genuinely manual, cannot be automated from this repo (🙋): F6, F8,
  G1 (uninstall-while-running half only), G4, G5.
- **4** special cases needing a hand-arranged device state (🧩): B14, C6,
  D8, E6.
- **1** deliberately out-of-scope group (🚫): H3-H8.

Plus an open-ended, separately-tracked set of one-off bugfix regression
cases (`scenarios/ALIV-*.md`, run via `test_case_runner.py`) not part of
this ID-by-ID matrix — see [`adding-a-test.md`](adding-a-test.md).
