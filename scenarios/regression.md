h4. A1: Creating New Config Files

1. Start the Accumate Application.
    Expected Result: _The application will open to a blank view._ *[PASS/FAIL]*

2. Click the top left circle button then hover your mouse over 'New'.
    Expected Result: _The options for new files will appear, 'AccuMate Config File' being one of them._ *[PASS/FAIL]*

3. Click on 'AccuMate Config File'.
    Expected Result: _The application will display a new AccuMate Config File._ *[PASS/FAIL]*

h4. A2: Saving Config Files

1. On the left side of the application window there will be an entry that says 'Config Directory'. If the button to the left of this is not a '-' and is instead a '+' click the button. After that click on 'System Layout'.
    Expected Result: _The system layout view will load successfully._ *[PASS/FAIL]*

2. At the top of the new view that loaded there will be an entry with the description of 'Number of Load Arms', double click on this row. (See image from previous step for location.)
    Expected Result: _The 'Edit Program Code Data' dialog will open._ *[PASS/FAIL]*

3. On the 'Edit Program Code Data' dialog edit the 'New' text area and change the 6 to a 3 then press OK.
    Expected Result: _The 'Edit Program Code Data' dialog will close and the 'Value' in the 'Number of Load Arms' row will be 3._ *[PASS/FAIL]*

4. In the top left of the window click on the Circle button then click 'Save' or 'Save as...'
    Expected Result: _The Save as window will open._ *[PASS/FAIL]*

5. Give the file a valid name and location then click 'Save'
    Expected Result: _The file will save successfully to the file system._ *[PASS/FAIL]*

6. In your file system explorer navigate to the file location and verify that it exists. 
    Expected Result: _The file will exist in the assigned location with the given name._ *[PASS/FAIL]*

h4. A3: Loading Current Al4 Config Files

1. Start the Accumate Application.
    Expected Result: _Expected Result The application will open to a blank view._ *[PASS/FAIL]*

2. In the top left click on the Circle button then click open.
    Expected Result: _The open File window will appear._ *[PASS/FAIL]*

3. Navigate to the .AL4 file and select it, then click 'Open'.
    Expected Result: _The AccuMate IV configuration file view will appear._ *[PASS/FAIL]*

h4. A4: Loading Old AL4 Config Files

1. A file C254_AL4_v0_4.AL4 is provided, which was created with Accuload0.4. Load this file, or proceed with steps 2-9 below.
    Expected Result: _Expected Result File is loaded, or created with steps 2-9 below._ *[PASS/FAIL]*

2. Open the AccuMate 4 v0.10 Application.

3. Create a new config file by selecting the "New AccuMate Document" button at the top of the application. The application will open to a blank view. 
    Expected Result: _A new AccuMate Configuration file is created and displayed in AccuMate._ *[PASS/FAIL]*

4. Select the "System Layout" directory on the left side of the application to bring up the System Layout configurations.
    Expected Result: _The System Layout configurations are displayed._ *[PASS/FAIL]*

5. Double click the "Number of Load Arms" description that appears on the main section of the application. An editing window will be displayed. Change the "New" value to "4" and the Security Level to "Level 5". When
    Expected Result: _The "Number of Load Arms" value has changed to 4 and the Security Level has changed to "Level 5"_ *[PASS/FAIL]*

6. Make these parameter changes to the following configurations:

*Pulse Inputs*

* Pulse In 01 -> Change the Pulse Input Tag to "PI01" and the Security Level to "Level 5" Pulse In 02 -> Change the Pulse Input Tag to "PI02"
  *Pulse Outputs*
* Pulse Out 01 -> Change the Pulse Output Tag to "PO01" and the Security Level to "Level 4" Pulse Out 02 -> Change the Pulse Output Tag to "PO02"
  *Digital Inputs*
  Dig In 01 -> Change Digital Input Tag to "DI01" and the Security Level to "Level 3" Dig In 02 -> Change Digital Input Tag to "DI02"

*Digital Outputs*
Dig Out 01 -> Change Digital Output Tag to "DO01" and the Security Level to "Level 2" Dig Out 02 -> Change Digital Output Tag to "DO02"

*Analog I/O*
Analog I/O 01 -> Change Analog I/O Tag to "A01" and the Security Level to "Level 5" Analog I/O 02 -> Change Analog I/O Tag to "A02"

*System Directory*

* General Purpose -> Change Unit ID to "Test" and the Security Level to "Level 4"
* Flow Control -> Change Solenoid Alarm Count to "1" and the Security Level to "Level 3"
* Volume Accuracy -> Change Pulse Transmitter Select to "Dual" and the Security Level to "Level 2"
* Temperature/Density -> Change Temperature Units to "F" and the Security Level to "Level 5"
* Pressure -> Change Pressure Units to "psi" and the Security Level to "Level 4"
* Security Directory -> Change Security Input 1 to "Digital Input 1" and switch the Security Level to "Level 3"
* Communications -> Serial Port -> Change Baud Rate under Serial Port 1 to "38400" and the Security Level to "Level 5"
* Communications -> Serial Port -> Change Baud Rate under Serial Port 2 to "2400"
* Additives -> Injectors -> Change the Injector Tag under Injector - 1 to "I01" and the Security Level to "Level 4"
* Additives -> Injectors -> Change the Injector Tag under Injector - 2 to "I02"
  *Arms*
  Arm 1 -> General Purpose -> Change Load Arm ID to "A1" and switch the Security Level to "Level 3"
  Arm 1 -> Meter 1 -> Flow Control -> Change Meter Tag to "A1M1" and switch the Security Level to "Level 2"
  Arm 1 -> Meter 1 -> Product 1 -> General Purpose -> Change Product ID to "A1M1P1" and switch the Security Level to "Level 5"
  Arm 2 -> General Purpose -> Change Load Arm ID to "A2"
  Arm 2 -> Meter 1 -> Flow Control -> Change Meter Tag to "A2M1"
  Arm 2 -> Meter 1 -> Product 1 -> General Purpose -> Change Product ID to "A2M1P1"

*Recipe Directory*
Recipe 01 -> Change Recipe Name to "R1" and switch the Security Level to "Level 4".
Recipe 02 -> Change Recipe Name to "R2"
    Expected Result: _All of the parameters listed are changed._ *[PASS/FAIL]*

7. Select the "Document Options" button at the top of the application inside the "Tools and Options" section.
    Expected Result: _The "Document Options" window is displayed._ *[PASS/FAIL]*

8. Change the IP address to a valid IP address (Remember it). Then change the order of the "Communications Addresses" to 1, 3, 4, 5, 6, and 2 from top to bottom. OK the dialog to save the changes.
    Expected Result: _The IP Address and the Communications Addresses are changed._ *[PASS/FAIL]*

9. Save the config file to a valid location on the machine. (Menu -> Save as...)
    Expected Result: _The older AccuMate configuration file is saved on the users machine._ *[PASS/FAIL]*

10. Switch over to the latest version of AccuMate.
    Expected Result: _The latest AccuMate version is now displayed._ *[PASS/FAIL]*

11. Go to the menu and select "Open" to open a file. Select the file created in the previous steps and open it. Verify that AccuMate is updating the file.
    Expected Result: _The older AccuMate file is opened inside AccuMate._ *[PASS/FAIL]*

12. Navigate through the configurations and verify that the changes made with the previous version of AccuMate have been loaded successfully into the latest version and no information was lost.
    Expected Result: _The parameter changes are successfully loaded into the latest version of AccuMate._ *[PASS/FAIL]*

13. Select "Document Options" at the top of the application. 
    Verify that the "IP address" and "Communications Addresses" changes are the same as it latest version of AccuMate.
    Expected Result: _The "Document Options" configuration was successfully loaded into the was in the previous version._ *[PASS/FAIL]*

*AL4 Configs Used/Created*

h4. A5: Loading A3X Config Files

1. Load the provided C255.A3X file, or follow steps 2-6 below.
    Expected Result: _Expected Result C255.A3X file exists_ *[PASS/FAIL]*

2. Start the Accumate 3 application.
    Expected Result: _The application will open to a blank view._ *[PASS/FAIL]*

3. Click in the top right 'File' then click 'New', then once click 'AccuLoadIII.NET data file'.
    Expected Result: _The AccuLoad.NET Wizard window will appear._ *[PASS/FAIL]*

4. Click 'Cancel' on the AccuLoad.NET Wizard window.
    Expected Result: _The Wizard window will disappear and a new configuration window will appear._ *[PASS/FAIL]*

5. In the window that appears double click on the row in the right part of the window that says 'Number of Load Arms'. Once the 'Edit Program Code Data' window appears change the 'New' field to be 5 and press 'OK'.
    Expected Result: _The 'Value' in the 'Number of Load Arms' row will change to 5._ *[PASS/FAIL]*

6. In the top of the AccuMate III window click 'File' then 'Save', give the file a valid name and location and then click 'Save'.
    Expected Result: _The AccuMate III config file (.A3X) will save to the file system._ *[PASS/FAIL]*

7. Start the Accumate 4 application.

8 In the top left click on the Circle button then click open. The application will open to a blank view.  Navigate to the AL3 configuration file (.A3X), select it, then click 'Open'.
    Expected Result: _The application will display the config file in the config editor._ *[PASS/FAIL]*

9. Compare the number of Load Arms.
    Expected Result: _These values will match in both views._ *[PASS/FAIL]*

*Config files created for this test*

h4. A6: Conversion Of Old AccuMate 4 Offsets

1. Load the existing file AL4 created with an earlier version of AccuMate IV or follow steps numbered 2-15 to create the file
    Expected Result: _Expected Result A06.AL4 is created_ *[PASS/FAIL]*

2. On the left side panel, expand the "Config Directory" section if it is not already expanded. Then expand the "Pulse Inputs" section and choose the element with the first offset.
    Expected Result: _The Pulse In 1 element is selected._ *[PASS/FAIL]*

3. Change the values of each parameter to the following: 
* Pulse Input Tag -> Pulse In 1 Pulse Input Function -> Meter Inj 1    

* Pulse Input Arm -> Arm 2

* Pulse Input Meter -> Meter 2
  Expected Result: _The first and second offset of the Pulse Input elements have different parameter values configured._ *[PASS/FAIL]*
4. Expand the Pulse Outputs section on the left panel of AccuMate. Select the first Offset and change its values to the following:
* Pulse Output Tag -> Pulse Out 1 

* Pulse Output Arm -> Arm1 Pulses 

* Pulse Out Meter -> Mtr1 Pulses 

* Pulse Out Pulses/Amount -> 1.11 

* Pulse Out Units -> GV Pulse Out Max Frequency -> 1
  Select Pulse Out 02 and change its configurations so they do not match the values of the first offset. Take a screenshot of the values used for the 2nd offset.
    Expected Result: _The first and second offset of the Pulse Output elements have different parameter values configured._ *[PASS/FAIL]*
5. Expand the Digital Inputs section on the left panel of AccuMate. Select the first Offset and change its values to the following:
* Digital Input Tag -> Digital Input 1

* Digital Input Function -> Permissive 1

* Digital Input Arm -> Arm 6

* Digital Input Product -> Product 2
  Select Dig In 02 and change its configurations so they do not match the values of the first offset. Take a screenshot of the values used for the 2nd offset.
    Expected Result: _The first and second offset of the Digital Input elements have different parameter values configured._ *[PASS/FAIL]*
6. Expand the Digital Outputs section on the left panel of AccuMate. Select
   the first Offset and change its values to the following:
* Digital Output Tag -> Digital Output 1

* Digital Output Function -> Pump

* Digital Output Arm -> Arm 2

* Digital Output Meter -> Meter 2

* Digital Output Product -> Product 2
  Select Dig Out 02 and change its configurations so they do not match the values of the first offset. Take a screenshot of the values used for the 2nd offset.
    Expected Result: _The first and second offset of the Digital Output elements have different parameter values configured._ *[PASS/FAIL]*
7. Expand the Analog I/O section on the left panel of AccuMate. Select the first Offset and change its values to the following:
* Analog I/O Tag -> Analog 1

* Analog I/O Function -> Temperature In

* Analog I/O Arm -> Arm 2

* Analog I/O Meter -> Meter 2

* Analog I/O Type -> 4-20 mA In

* Analog I/O Cal 1 -> 12200

* Analog I/O Cal 2 -> 52896

* Analog I/O Low Value -> -1.00

* Analog I/O High Value -> 1.00

* Analog I/O RTD Offset -> -1.00
  Select Analog I/O 02 and change its configurations so they do not match the values of the first offset. Take a screenshot of the values used for the 2nd offset.
    Expected Result: _The first and second offset of the Analog I/O elements have different parameter values configured._ *[PASS/FAIL]*
8. Expand the "System Directory" section on the left panel. Then expand "Communications". Select the "Serial Port" option and the configurations parameter values configured will be shown in AccuMate. There should be multiple offsets shown on screen; under "Serial Port - 1", change the following parameter values:
* Function -> MiniComp Host

* Baud Rate -> 57600

* Data/Parity -> 8 Data No Parity

* Control -> Poll & Program

* Timeout -> 30

* Serial Interface -> RS-485

* RS8-485 Duplex -> Half Duplex

* Termination Resistors -> Enabled
  Under "Serial Port - 2", change the parameter values so the configurations for both offsets are different from each other. Take a screenshot of the values used for the 2nd offset.
    Expected Result: _The first and second offset of the Serial Port elements have different parameter values configured._ *[PASS/FAIL]*
9. Expand the Arm 1 section on the left panel. Select "General Purpose" and change the following parameter values:
* Permissive 1 Message -> This is a test

* Permissive 1 Restart -> Auto

* Ready Message -> AccuLoad IV Test
  Under "Arm 2" -> "General Purpose", change the parameter values so the listed configurations for both offsets are different from each other. Take a screenshot of the values used for the 2nd offset.
    Expected Result: _The first and second offset of the Arm elements have different_ *[PASS/FAIL]*
10. Under Arm 1, there should be multiple Meters, expand Meter 1 and select
    "Flow Control". Change the following parameters:
* Meter Tag -> Meter Test 1

* Meter 1 and Meter 2 have different configured values.

* Valve Type -> Analog

* Analog Valve Kp -> 1.000

* Analog Valve Ki -> 2.000

* Analog Valve Kd -> 3.000
  Expand the Meter 2 section under the same Arm. Select "Flow Control" and change the same parameters mentioned above for Meter 2, but make the parameters for Meter 2 have different values than the parameters in Meter 1. Take a screenshot of the values used for the 2nd offset.
11. Expand the Arm 2 section on the left panel. Expand Meter 1, then Product Product 1 and Product 2 have different configured values.
    Select the "General Purpose" option to bring up some configurations. Change the following parameter values:
* Product ID -> Product 1

* HM Class Part 1 -> Part 1

* HM Class Part 2 -> Part 2
  Once completed, expand the Product 2 section on the left panel. Select "General Purpose" and change the configurations so it does not match the Product 1 configuration. Take a screenshot of the values used for the 2nd offset.
12. Expand the "Recipe Directory" section on the left side panel. Select Recipe 01 to bring up its configurations (Make sure Recipe 01 is highlighted and NOT Recipe Injectors). Change the following parameter values:
* Recipe Used -> Load Arm 2

* Recipe Name -> Test Recipe 1

* HM Class Product -> Product 2

* 1st Delivered -> Product 2
  Now select Recipe 02 in the Recipe Directory; change the same parameters listed above, but be sure to not use the same values. Take a screenshot of the values used for the 2nd offset.
    Expected Result: _Recipe 01 and Recipe 02 have different configured values._ *[PASS/FAIL]*
13. Expand Recipe 01 to reveal "Recipe Injectors". Select Recipe Injectors to bring up a list of Injector. Under Injector Offset 1 (Injector - 1), change the following parameter values:
* Additive Amount/Cycle -> 1.000

* Additive Rate -> 1.0

* Products Using Additive -> Product 2
  Do the same thing for the Injector - 1 configuration under the Recipe 02 section, but make sure the configuration for this offset is different from Recipe 01's Injector - 1 configuration. Take a screenshot of the values used for the Recipe 02 offset.
    Expected Result: _The Recipe 01 and Recipe 02 injectors have different configured values._ *[PASS/FAIL]*
14. Navigate to the "Recipe Injectors" configuration for Recipe 01. Notice how there are multiple injectors in this section labeled "Injector - #". The previous step has already updated the data under Injector - 1, now Injector - 2 needs to be tested; make changes to the parameter values for this offset. Verify that both "Injector - 1" and "Injector - 2" have different configurations for each parameter. Take a screenshot of the Injector - 2 configuration for verification purposes later on in the test.
    Expected Result: _The Injector - 1 and Injector - 2 offsets have different configured values._  *[PASS/FAIL]*

15. Save the configuration file to a valid location. Exit the older version of
    AccuMate IV and open up the latest version.
    Expected Result: _The configuration file of the older AccuMate IV version is saved. The latest version of AccuMate is open._ *[PASS/FAIL]*

16. Open up the configuration file that was just saved into the latest version
    of AccuMate. Allow AccuMate to update the configuration file.
    Expected Result: _The configuration file is opened up in AccuMate._ *[PASS/FAIL]*

17. Navigate to the Pulse Inputs section on the left panel. Review the Pulse In 01 and Pulse In 02 offsets. Verify that the parameter values for both offsets are the same as they were when created in step 2. Take a screenshot of both offsets. Post the screenshots from this step (And step 2) in the test run.
    Example: Pulse In 01:
    Expected Result: _The 2nd offset did not clone the data from the 1st offset and the values are the exact same as they were in the older version of AccuMate._ *[PASS/FAIL]*

18. Navigate to the Pulse Outputs section on the left panel. Review the Pulse The 2nd offset did not clone the data from the 1st offset and the values Out 01 and Pulse Out 02 offsets. Verify that the parameter values for both are the exact same as they were in the older version of AccuMate. offsets are the same as they were when created in step 3. Take a screenshot of both offsets. Post the screenshots from this step (And step 3) in the test run.

19. Navigate to the Digital Inputs section on the left panel. Review the Dig In The 2nd offset did not clone the data from the 1st offset and the values 01 and Dig In 02 offsets. Verify that the parameter values for both offsets are the exact same as they were in the older version of AccuMate. are the same as they were when created in step 4. Take a screenshot of both offsets. Post the screenshots from this step (And step 4) in the test run.

20. Navigate to the Digital Outputs section on the left panel. Review the Dig Out 01 and Dig Out 02 offsets. Verify that the parameter values for both offsets are the same as they were when created in step 5. Take a screenshot of both offsets. Post the screenshots from this step (And step 5) in the test run.
    Expected Result: _The 2nd offset did not clone the data from the 1st offset and the values are the exact same as they were in the older version of AccuMate._ *[PASS/FAIL]*

21. Navigate to the Analog I/O section on the left panel. Review the Analog I/O 01 and Analog I/O 02 offsets. Verify that the parameter values for both are the exact same as they were in the older version of AccuMate. Take a screenshot of both offsets. Post the screenshots from this step (And step 6) in the test run.
    Expected Result: _The 2nd offset did not clone the data from the 1st offset and the values offsets are the same as they were when created in step 6. *[PASS/FAIL]*

22. Navigate to the Serial Port section on the left panel (Expand System Directory -> Communications). Review the 1st and 2nd Serial Port are the exact same as they were in the older version of AccuMate.  Verify that the parameter values for both offsets are the same as they were when created in step 7. Take a screenshot of both offsets. Post the screenshots from this step (And step 7) in the test run.
    Expected Result:  The 2nd offset did not clone the data from the 1st offset and the values offsets. *[PASS/FAIL]* 

23. Navigate to the Arm 1 section on the left panel and review the data in the General Purpose section; do the same for Arm 2. Verify that the parameter values for both offsets are the same as they were when created in step 8. Take a screenshot of both offsets. Post the screenshots from this step (And step 8) in the test run.
    Expected Result: _The 2nd offset did not clone the data from the 1st offset and the values are the exact same as they were in the older version of AccuMate._ *[PASS/FAIL]*

24. Navigate to the Arm 1 section on the left panel and expand the Meter 1 and Meter 2 sections. Verify that the Flow Control parameter configurations for both offsets are the same as they were when created in step 9. Take a screenshot of both offsets. Post the screenshots from this step (And step 9) in the test run.
    Expected Result: _The 2nd offset did not clone the data from the 1st offset and the values are the exact same as they were in the older version of AccuMate._ *[PASS/FAIL]*

25. Navigate to the Arm 2 section on the left panel and go to the Product offsets under Meter 1. Verify that the General Purpose configurations for both offsets are the same as they were when created in step 10. Take a screenshot of both offsets. Post the screenshots from this step (And step 10) in the test run.
    Expected Result: _The 2nd offset did not clone the data from the 1st offset and the values are the exact same as they were in the older version of AccuMate._ *[PASS/FAIL]*

26. Expand the Recipe Directory and review the configurations for Recipe 01 and Recipe 02. Compare the configurations displayed with the configurations from step 11. Verify that the configurations did not change for either of the Recipes. Take a screenshot of both offsets. Post the screenshots from this step (And step 11) in the test run.
    Expected Result:  The 2nd offset did not clone the data from the 1st offset and the values are the exact same as they were in the older version of AccuMate. *[PASS/FAIL]*

27. Expand the Recipe 01 and Recipe 02 sections on the left panel. Select the Recipe Injectors option for both Recipes and verify that the configuration changes made in step 12 are still saved. Take a screenshot of both configurations. Post the screenshots from this step (And step 12) in the test run.
    Expected Result: _The 2nd offset did not clone the data from the 1st offset and the values are the exact same as they were in the older version of AccuMate._ *[PASS/FAIL]*

h4. A7: Manually Connecting to an AccuLoad

1. Start the AccuMate Application.
    Expected Result: _Expected Result The application will open to a blank view._ *[PASS/FAIL]*

2. Click the top left circle button then hover your mouse over 'New'.
    Expected Result: _The options for new files will appear, 'AccuMate Config File' being one of them._ *[PASS/FAIL]*

3. Click on 'AccuMate Config File'.
    Expected Result: _The application will display a new AccuMate Config File._ *[PASS/FAIL]*

4. Click on 'Document Options' in the top ribbon.
   Enter in the IP address of the target AccuLoad instance and OK the dialog. 'ONLINE' will be in the bottom right corner to the left of 'TCP/IP: X.X.X.X' (X.X.X.X being the IP address you entered.)
    Expected Result: _The AccuMate will connect successfully to the target AccuLoad, _ *[PASS/FAIL]*

h4. A8: Automatically Connecting to an AccuLoad

1. Start the AccuMate Application.
    Expected Result: _Expected Result The application will open to a blank view._ *[PASS/FAIL]*

2. In the top left click on the Circle button then click open. Navigate to the .AL4 file and select it.
    Expected Result: _The application will display the configuration. The application will also connect to the target AccuLoad which will be shown in the bottom right of the main frame._ *[PASS/FAIL]*

h4. A9: Valid Arm Addresses

1. Start the Accumate application.
    Expected Result: _Expected Result The application will open to a blank view._ *[PASS/FAIL]*

2. Click the top left circle button then hover your mouse over 'New'.
   Click on 'AccuMate Config File'.
    Expected Result: _The application will display a new AccuMate Config File._ *[PASS/FAIL]*

3. Open Document Options in the top ribbon. Enter in the IP address of the target AccuLoad instance and OK the dialog.
    Expected Result: _The AccuMate will connect successfully to the target AccuLoad._ *[PASS/FAIL]*

4. Open Document Options again and change Arm Address 1 to 0. OK the
   dialog.
    Expected Result: _The dialog will throw a warning that arm address 1 cannot be 0._ *[PASS/FAIL]*

5. Open Document Options again and change Arm 1 address to 1. Change
   Arm Address 2 to 0. OK the dialog.
    Expected Result: _The dialog will close, but the view will throw a warning that Arm Address 2 is configured for use, and advise the user to change the address of Arm 2._ *[PASS/FAIL]*

h4. A10: Pushing Full Configurations

1. Start the AccuMate application.
    Expected Result: _Expected Result The application will open into a blank view._ *[PASS/FAIL]*

2. In the top left click on the Circle button then click open. Navigate to the AccuLoad IV configuration file (.AL4) and select it, then click 'Open'.
    Expected Result: _The view will display the target config file._ *[PASS/FAIL]*

3. Be sure that AccuMate is NOT connected to the AccuLoad at this point.  On the left side section of AccuMate, navigate down to "Config Directory"-> "Pulse Inputs" -> "Pulse In 01".   The "Pulse In 01" information should be displayed. Select one of the elements and change the value to a different
    Expected Result: _The value will be changed successfully._ *[PASS/FAIL]*

4. On the left side section of AccuMate, navigate down to "System Directory" -> "Communications". The "Communications" information should be displayed. Change the following parameters if necessary: 
* IP Discovery -> Manual 

* IP Address -> AccuLoad's IP Address 

* Netmask -> 255.255.0.0 

* Gateway -> 10.1.1.1
5. Click on 'Document Options' in the top ribbon. Enter in the IP address of the target AccuLoad instance and OK the dialog.
    Expected Result: _The IP Discovery, IP Address, Netmask, and Gateway are set to the correct values.  The AccuMate will connect successfully to the target AccuLoad._ *[PASS/FAIL]*

6. Click on 'Push All to AccuLoad' in the top Ribbon under 'Import/Export
   configurations to/from the AccuLoad'

7. Switch over to the AccuLoad application that the AccuMate was connected to.

8. Navigate to "Program Mode" -> "Config" -> "Pulse Inputs" -> "Pulse In 1".

9. Verify that the change made on the AccuMate was successfully pushed up to the AccuLoad application.  The AccuMate will push the full configuration from the config file to the target AccuLoad. The user is now using the AccuLoad application.
    Expected Result: _The AccuLoad is displaying the "Pulse In 1" screen. The change is successfully changed from the Push._ *[PASS/FAIL]*

10. Navigate to Program Mode -> Communications -> Host Interface and verify the IP, Netmask, and Gateway information has change to match the AccuMate configuration.
    Expected Result: _The IP Address, Netmask, and Gateway info is correct._ *[PASS/FAIL]*

h4. A11: Pulling Full Configurations

1. Start the AccuMate application.
    Expected Result: _Expected Result The application will open into a blank view._ *[PASS/FAIL]*

2. Click the top left circle button then hover your mouse over 'New'.
   Click on 'AccuMate Config File'.
    Expected Result: _The application will display a new AccuMate Config File._ *[PASS/FAIL]*

3. Switch over to the AccuLoad UI index page and navigate to the "Program Mode" screen.
    Expected Result: _The AccuLoad application will be displaying the "Program Mode" screen._ *[PASS/FAIL]*

4. Navigate to "Config" -> "System Layout".

5. Select the value for "Arm 1 Configuration" and change it to any other value. When you choose a new value, click submit.
    Expected Result: _The AccuLoad application will be displaying the "System Layout" screen. The value of the "Arm Configuration" is changed to a different value._ *[PASS/FAIL]*

6. Navigate back to the "Config" screen and navigate to the "Pulse Inputs"
   screen.
    Expected Result: _The AccuLoad application will be displaying the "Config" screen._ *[PASS/FAIL]*

7. Select the first option on the screen, "Pulse In 1" (Top left of the screen). 
    Expected Result: _The AccuLoad application will be displaying the screen for Pulse In 1._ *[PASS/FAIL]*

8. Select the value for the "Pulse Input Tag" and change it to "test". 
    Expected Result: _The Pulse Input Tag will have the "test" value. _ *[PASS/FAIL]*

9. Navigate back to "Program Mode" and navigate to the "Arms" screen.
    Expected Result: _The AccuLoad application will be displaying the "Arms" screen._ *[PASS/FAIL]*

10. Select "Arm 1".
    Expected Result: _The AccuLoad application will be displaying the "Arm 1" screen._ *[PASS/FAIL]*

11. Select the "General Purpose" option.
    Expected Result: _The "General Purpose" screen for Arm 1 is displayed with descriptions and values._ *[PASS/FAIL]*

12. Select the "Permissive 1 Sense" value and change it to a different value.
    Expected Result: _The "Permissive 1 Sense" value is changed._ *[PASS/FAIL]*

13. Navigate back to "Program Mode" and save the changes by clicking the green button. (If an additional window appears showing critical errors, click the "Logout with Fatal" option)
    Expected Result: _The changes to the AccuLoad will be saved._ *[PASS/FAIL]*

14. Switch over to the AccuMate application. Select the "Document Options" button on the top of the page in the "Tools and Options" section. Switch
    Expected Result: _The AccuMate will connect to the AccuLoad._ *[PASS/FAIL]*

15. Select the "Pull All from AccuLoad" button at the top of the AccuMate and wait for the AccuLoad changes to be pulled to AccuMate.
    Expected Result: _The changes to the AccuLoad will be pulled into AccuMate application._ *[PASS/FAIL]*

16. On the left side of the AccuMate application, select "System Layout" under the "Config Directory" element and verify that the change to "Arm 1 Configuration" was pulled down.
    Expected Result: _The "Arm 1 Configuration" value change was successfully pulled down into AccuMate._ *[PASS/FAIL]*

17. On the left side, expand the "Config Directory" element if it is not already. Then expand the "Pulse Inputs" element. Select the "Pulse In 01" element and verify that the change made to the "Pulse Input Tag" was pulled down from the AccuLoad.
    Expected Result: _The "Pulse Input Tag" value was successfully pulled down from the AccuLoad._ *[PASS/FAIL]*

18. On the left side, expand the "Arm 1" element and select the "General Purpose" option. Verify that the "Permissive 1 Sense" value is the same
    Expected Result: The "Permissive 1 Sense" value was successfully pulled from the AccuLoad._ *[PASS/FAIL]*

AccuMate IV Config File generated from this test:

h4. A12: Pushing Selected Configurations

1. Start the Accumate application.
    Expected Result: _Expected Result The application will open into a blank view._ *[PASS/FAIL]*

2. Click the top left circle button then hover your mouse over 'New'. Click on 'AccuMate Config File'.
    Expected Result: _The application will display a new AccuMate Config File._ *[PASS/FAIL]*

3. Under 'Config Directory' on the left, press the '+' sign to the left of the green arrow if it is there, if it is a '-' sign proceed.  Click 'System Layout' then double click on 'Number of Load Arms' in the view that appeared to the right and change the 'New' text field to be a different value.
    Expected Result: _The value for Number of Load Arms will change to a different value._ *[PASS/FAIL]*

4. On the left side section in AccuMate, navigate to "Digital Inputs" -> "Dig In 01".
    Expected Result: _The information for the Dig In 01 will be displayed._ *[PASS/FAIL]*

5. Select one of the values that you want to make changes for. Change the value in the "New" element field on the popup that appears and OK the changes.
    Expected Result: _The selected element will have its value changed successfully._ *[PASS/FAIL]*

6. On the left section of the AccuMate, select the "System Layout" element. The "System Layout" element is selected and the information is displayed.  (This will be the information we want to push up to the AccuLoad)

7. Click on 'Document Options' in the top ribbon.  Enter in the IP address of the target AccuLoad instance and OK the dialog.
    Expected Result: _The AccuMate will connect successfully to the target AccuLoad._ *[PASS/FAIL]*

8. Select the "Push Selected to AccuLoad" button. The AccuMate will begin to push the changes made in the "System Layout" section.
    Expected Result: _The changes to "System Layout" are pushed to the AccuLoad successfully with no errors._ *[PASS/FAIL]*

9. When the Pushing process is complete, switch over to the AccuLoad application and navigate to the index screen.

10. Navigate to "Program Mode" -> "Config" -> "System Layout". Verify that the "Number of Load Arms" value is the same value as set  in AccuMate.
    Expected Result: _The value for the "Number of Load Arms" will match what was changed in AccuMate._ *[PASS/FAIL]*

11. Navigate back to the "Config" screen. Once there, navigate to "Digital Inputs" -> "Digital Input 1". Verify that the change made to Digital Input did not get pushed up to the AccuLoad.
    Expected Result: _The value changed in AccuMate was not updated on the AccuLoad._ *[PASS/FAIL]*

AccuMate Config Created/Used in this test:

h4. A13: Pulling Selected Configurations

1. Start the Accumate application.
    Expected Result: _The application will open into a blank view._ *[PASS/FAIL]*

2. Open a new AccuMate Config File.
    Expected Result: _A new AccuMate Configuration file is presented on screen._ *[PASS/FAIL]*

3. Switch over to the AccuLoad application in the browser.

4. Navigate to Program Mode -> Config -> Pulse Inputs -> Pulse In 1 (First option). 
    Expected Result: _The application should be showing the values for Pulse In 1._ *[PASS/FAIL]*

5. Switch the "Pulse Input Function" value to a different value.  The user is looking at the AccuLoad application. The application is displaying the "Pulse In 1" details screen. 
    Expected Result: _The "Pulse Input Function" value is changed to a different value._ *[PASS/FAIL]*

6. Navigate back to the "Config" screen and navigate to Pulse Outputs ->
   Pulse Out 1.
    Expected Result: _The application should be displaying the "Pulse Out 1" screen._ *[PASS/FAIL]*

7. Switch the "Pulse Output Tag" value to a different value.
    Expected Result: _The value for the "Pulse Output Tag" is changed._ *[PASS/FAIL]*

8. Navigate all the way back to the Program Mode screen and select "Save and Exit". If the "Critical Errors" screen appears, just click "Logout with Fatal".

9. Switch back to the AccuMate application and connect to the AccuLoad by inputing the IP address inside "Document Options".
    Expected Result: _The changes made to the AccuLoad will be saved. AccuMate will successfully connect to the AccuLoad._ *[PASS/FAIL]*

10. Select the "Pulse Inputs" element on the left side of the AccuMate application. This will be the data AccuMate will pull down from the AccuLoad.
    Expected Result: _The "Pulse Inputs" element is selected._ *[PASS/FAIL]*

11. Select the "Pull selected from AccuLoad" and wait for the pulling process to complete.
    Expected Result: _The Pulse Inputs information from the AccuLoad is successfully pulled into the AccuMate application._ *[PASS/FAIL]*

12. Under the Pulse Inputs element, select "Pulse In 01" and validate that the change made to the information on the AccuLoad was successfully pulled and updated onto the AccuMate.
    Expected Result: _The "Pulse Input Function" value has been updated with the change from the AccuLoad._ *[PASS/FAIL]*

13. Under the Pulse Outputs element, select "Pulse Out 01" and verify that the change made to the "Pulse Output Tag" value was not pulled from
    Expected Result: _The value did not update with the change because AccuMate did not pull information about the Pulse Outputs._ *[PASS/FAIL]*

AccuMate config Created/Used here:

h4. A14: Downloading Totalizers

1. Start the AccuMate Application.

2. Click the top left circle button then hover your mouse over 'New'.  Click on 'AccuMate Config File'.  The application will display a new AccuMate Config File.
    Expected Result: _The application will open to a blank view. _ *[PASS/FAIL]*

3. Click on 'Document Options' in the top ribbon.
   Enter in the IP address of the target AccuLoad instance and OK the dialog.
    Expected Result: _The AccuMate will connect successfully to the target AccuLoad._ *[PASS/FAIL]*

4. Click on 'Retrieve Totalizers' in the top ribbon.
    Expected Result: _The application will download totalizers from the target Accuload and display them in a new view._ *[PASS/FAIL]*

h4. A15: Changing Values in a Config

1. Start the AccuMate Application.

2. Click the top left circle button then hover your mouse over 'New'.  Click on 'AccuMate Config File'.
    Expected Result: _The application will open to a blank view. The application will display a new AccuMate Config File._ *[PASS/FAIL]*

3. Under 'Config Directory' on the left, press the '+' sign to the left of the green arrow if it is there, if it is a '-' sign proceed.  Click 'System Layout' then double click on 'Number of Load Arms' in the view that appeared to the right and change the 'New' text field to be 3 instead of 6 then press okay.
    Expected Result: _The value for Number of Load Arms will change to 3 and the tree on the left of the view will drop arms 4-6._ *[PASS/FAIL]*

h4. A16: Calling Help

1. Start the AccuMate Application.

2. Click on the Help button at the top-right corner of the application.
    Expected Result: _The application will open to a blank view. The Help dialog will be displayed._ *[PASS/FAIL]*

3. Click the '+' sign next to 'Using AccuMate' then click on 'Using the
   Language Editor'.
    Expected Result: _The dialog will display the help page for the translation editor._ *[PASS/FAIL]*

4. Navigate to the following and verify that the help page appears for each
   of them: - Using the Configurable Report Editor - Using the Equation Set Editor - Using the Database Editor
    Expected Result: _The dialog will display the help page for each of the other editors._ *[PASS/FAIL]*

h4. A17: Calling Context Help

1. Start the AccuMate Application.

2. Open a new config file.
    Expected Result: _The application will open to a blank view. The application will display a new configuration._ *[PASS/FAIL]*

3. Navigate to "Recipe Directory"->"Recipe 01"->"HM Class Product" then double click the row to open the 'Edit Program Code Data' window.
    Expected Result: _The dialog for editing the value will open._ *[PASS/FAIL]*

4. Click the Help button.
    Expected Result: _The Help dialog will open, displaying the relevant page for "HM Class Product"._ *[PASS/FAIL]*

h4. A18: Smithcomm "HI"

1. Start the Accumate application.
    Expected Result: _The application will open into a blank view._ *[PASS/FAIL]*

2. Open a new config file.
    Expected Result: _The view will display the config file._ *[PASS/FAIL]*

3. Click on 'Document Options' in the top ribbon.  Enter in the IP address of the target AccuLoad instance and OK the dialog.
    Expected Result: _The AccuMate will connect successfully to the target AccuLoad._ *[PASS/FAIL]*

4. Open the Terminal Emulator by clicking on 'Terminal Emulator' in the top
   ribbon.
    Expected Result: _A new view will appear to send commands to the Accuload._ *[PASS/FAIL]*

5. Enter the command "HI" into the Terminal Emulator.
    Expected Result: _The Accuload will respond with identifying information, confirming the connection._ *[PASS/FAIL]*

h4. A19: Terminal PUSH Command

1. Start the AccuMate application.
    Expected Result: _The application will open into a blank view._ *[PASS/FAIL]*

2. Click the top left circle button then hover your mouse over 'New'.  Click on 'AccuMate Config File'.
    Expected Result: _The application will display a new AccuMate Config File._ *[PASS/FAIL]*

3. Click on 'Document Options' in the top ribbon.
   Enter in the IP address of the target AccuLoad instance and OK the dialog.
    Expected Result: _The AccuMate will connect successfully to the target AccuLoad._ *[PASS/FAIL]*

4. Open the Terminal Emulator by clicking the 'Terminal Emulator' button in the top ribbon under 'Tools and Options'.
    Expected Result: _The Terminal Emulator view will appear._ *[PASS/FAIL]*

5. Enter the command "PUSH" into the emulator by typing into the text box and then pressing enter.
    Expected Result: _The application will parse this command as a request to push all configuration settings to the Accuload, and begin pushing that information._ *[PASS/FAIL]*

h4. A20: Terminal PULL Command

1. Start the Accumate application.
    Expected Result: _The application will open into a blank view._ *[PASS/FAIL]*

2. Click the top left circle button then hover your mouse over 'New'.  Click on 'AccuMate Config File'.
    Expected Result: _The application will display a new AccuMate Config File._ *[PASS/FAIL]*

3. Click on 'Document Options' in the top ribbon.  Enter in the IP address of the target AccuLoad instance and OK the dialog.
    Expected Result: _The AccuMate will connect successfully to the target AccuLoad._ *[PASS/FAIL]*

4. Open the Terminal Emulator by clicking the 'Terminal Emulator' button in the top ribbon under 'Tools and Options'.
    Expected Result: _The Terminal Emulator view will appear._ *[PASS/FAIL]*

5. Enter the command "PULL" into the emulator by typing into the text box and then pressing enter.
    Expected Result: _The application will parse this command as a request to pull all configuration settings from the Accuload, and begin pulling that information._ *[PASS/FAIL]*

h4. A21: Going Offline

1. Start the AccuMate Application.
    Expected Result: _The application will open to a blank view._ *[PASS/FAIL]*

2. Click the top left circle button then hover your mouse over 'New'.  Click on 'AccuMate Config File'.
    Expected Result: _The application will display a new AccuMate Config File._ *[PASS/FAIL]*

3. Click on 'Document Options' in the top ribbon.  Enter in the IP address of the target AccuLoad instance and OK the dialog.
    Expected Result: _The AccuMate will connect successfully to the target AccuLoad._ *[PASS/FAIL]*

4. Click the 'Go Online' button located in the top ribbon under Tools and Options.
    Expected Result: _The Accumate will disconnect from the AccuLoad and display this new connection status in the bottom status bar._ *[PASS/FAIL]*

h4. A22: Retrying Communication

1. Start the AccuMate Application.
    Expected Result: _The application will open to a blank view._ *[PASS/FAIL]*

2. Open a new config file.
    Expected Result: _The application will display a new configuration._ *[PASS/FAIL]*

3. Click on 'Document Options' in the top ribbon.  Enter in the IP address of the target AccuLoad instance and OK the dialog.
    Expected Result: _The AccuMate will connect successfully to the target AccuLoad._ *[PASS/FAIL]*

4. Click the 'Go Offline' button located in the top ribbon under Tools and Options.
    Expected Result: _The Accumate will disconnect from the AccuLoad and display this new connection status in the bottom status bar._ *[PASS/FAIL]*

5. Click Retry Comm.
    Expected Result: _The Accumate will successfully re-establish communication with the Accuload that was disconnected._ *[PASS/FAIL]*

h4. A23: General Options - Print Security Level

1. Open up the "General Options" dialog window.
    Expected Result: _The "General Options" window is open._ *[PASS/FAIL]*

2. Inside the "Printing Options" section, select the "Include security level on printout" option. Then OK the dialog.
    Expected Result: _The "Include security level on printout" box is enabled._ *[PASS/FAIL]*

3. Navigate to the drop down menu by selecting the circle button at the top left of the screen. Select the Print option.
    Expected Result: _The "Print" window is displayed._ *[PASS/FAIL]*

4. If it is not already, change the "Name" value to "Microsoft Print to PDF".  Then OK the dialog.
    Expected Result: _AccuMate is set to print to PDF._ *[PASS/FAIL]*

5. Choose a valid location and name for the PDF file. Then click save.

6. Navigate to the location of the PDF file saved in the previous step.
   View the file and verify that the Security Levels column is visible.
    Expected Result: _The PDF is saved to the chosen location. The Security Levels column is included in the PDF._ *[PASS/FAIL]*

7. Repeat steps 1-5 again, but this time, disable "Include security level on printout".

8. Navigate to the PDF location.  View the file and verify that there isn't a column for Security Levels.
    Expected Result: _The PDF is saved without a Security Level column. There is no column for security levels._ *[PASS/FAIL]*

h4. A24: General Options - Display Security Level

1. Take note of the Security Level column in the Config File.  Select the "General Options" option in the "Tools and Options" section.
    Expected Result: _The "General Options" window is displayed._ *[PASS/FAIL]*

2. Disable the "Display security level in parameter list view" option inside the "Program Code List View Options" section. (Uncheck the box) Then OK the dialog.
    Expected Result: _The "Display security level in parameter list view" option is disabled._ *[PASS/FAIL]*

3. Verify that the "Security Level" column is not displayed in the list view.
    Expected Result: _The "Security Level" column is not displayed._ *[PASS/FAIL]*

h4. A25: General Options - Print Unused Recipes

1. Open up the "General Options" dialog window.
    Expected Result: _The "General Options" window is open._ *[PASS/FAIL]*

2. Inside the "Printing Options" section, select the "Suppress printing unused recipes" option. Then OK the dialog.
    Expected Result: _The "Suppress printing unused recipes" box is enabled._ *[PASS/FAIL]*

3. While looking at the config file in AccuMate, navigate to the "Recipe Directory" section on the left side container.
    Expected Result: _The "Recipe Directory" is expanded._ *[PASS/FAIL]*

4. Select a recipe to see its configuration on screen.  Keep going through the recipes until there is a recipe that has its "Recipe Used" value set to "Not Used". (If all of the recipes are in use, change the value of one of the recipes to "Not Used")  Take note of this recipe number.
    Expected Result: _A recipe is not being used._ *[PASS/FAIL]*

5. Navigate to the drop down menu by selecting the circle button at the top left of the screen. Select the Print option.
    Expected Result: _The "Print" window is displayed._ *[PASS/FAIL]*

6. If it is not already, change the "Name" value to "Microsoft Print to PDF".  Then OK the dialog.
    Expected Result: _AccuMate is set to print to PDF._ *[PASS/FAIL]*

7. Choose a valid location and name for the PDF file.  Then click save.
    Expected Result: _The PDF is saved to the chosen location._ *[PASS/FAIL]*

8. Navigate to the location of the PDF file saved in the previous step.  View the PDF and search for the recipe that was not being used. (Can use "Ctrl + F")  Verify that there is no information about the unused recipe in the PDF.
    Expected Result: _The unused recipe is not included in the PDF._ *[PASS/FAIL]*

9. Repeat steps 1-7 again, but this time, disable the "Suppress printing
   unused recipes" option.
    Expected Result: _The Config File is printed to the PDF with the "Suppress printing unused recipes" option disabled._ *[PASS/FAIL]*

10. Navigate to the location of the PDF file saved in the previous step.  View the PDF and search for the recipe that was not being used. (Can use "Ctrl + F")
    Expected Result: _The unused recipe is included in the PDF._ *[PASS/FAIL]*

h4. A26: General Options - Limit Printout

1. Open up the "General Options" dialog window.
    Expected Result: _The "General Options" window is open._ *[PASS/FAIL]*

2. Inside the "Printing Options" section, select the "Limit printout of parameters to:" drop-down menu and select "Print All". Then OK the dialog.
    Expected Result: _The "Print All" value is selected._ *[PASS/FAIL]*

3. Take note of at least 1 element from each security level from the Config File. These elements will be used to verify which security levels were printed into the PDF.  Navigate to the drop down menu by selecting the circle button at the top left of the screen. Select the Print option.
    Expected Result: _The "Print" window is displayed._ *[PASS/FAIL]*

4. If it is not already, change the "Name" value to "Microsoft Print to PDF".
    Expected Result: _AccuMate is set to print to PDF._ *[PASS/FAIL]*

5. Choose a valid location and name for the PDF file.  Then click save.
    Expected Result: _The PDF is saved to the chosen location._ *[PASS/FAIL]*

6. Navigate to the location of the PDF file saved in the previous step.  View the PDF and verify that an element of each security level is included in the PDF.
    Expected Result: _All elements are included in the PDF file._ *[PASS/FAIL]*

7. Repeat steps 1-5 for all of the values in the "Limit printout of parameters to:" drop-down menu. Verify that for each print, the specified security levels are the only ones printed to the PDF.
   Example:
   "Level 2 and above" should only print elements with a security level of 2 or higher. "Level 3 and above" should only print elements with a security level of 3 or higher. "Level 4 and above" should only print elements with a security level of 4 or higher. "Level 5" should only print security level 5 elements into the PDF.
    Expected Result: _The PDF only includes the elements of the specified security level(s)._ *[PASS/FAIL]*

PDF files created during this test:

h4. A27: Document Options - Default IP

1. Navigate to "Document Options" inside the "Tools and Options" section.
    Expected Result: _The "Document Options" window is displayed._ *[PASS/FAIL]*

2. Verify that the "IP Address" value is set to the "192.168.0.1" IP address.
    Expected Result: _The default IP address is correct._ *[PASS/FAIL]*

h4. B1: Creating New Report Files

1. Start the Accumate Application.
2. Click the top left circle button then hover your mouse over 'New'.
   Expected Result The application will open to a blank view.
    Expected Result: _The options for new files will appear, 'Report Configuration' being one of them._ *[PASS/FAIL]*
3. Click on 'Report Configuration'.

h4. B2: Saving Report Files

1. Under 'Edit Options' in the top ribbon, click 'Insert'.
    Expected Result: _A New Item text field will be placed on the report and the 'Edit Report Item' window will open._ *[PASS/FAIL]*

2. Enter in text to 'Item Value' text area then click OK.
    Expected Result: _The Text Field on the report will contain the new text._ *[PASS/FAIL]*

3. Repeating step one, press 'Insert'. Change the 'Line' text field to '2'.
   Change the 'Item Type' to Run/Program Data Value then click 'Change'. Once the 'Select Data Item' window opens expand 'Load Arm Layout' and click 'Number of Load Arms'. Press OK twice.
    Expected Result: _The number of Load Arms will be loaded onto the report view as a Text Field._ *[PASS/FAIL]*

4. Repeating step one, press 'Insert'. Change the 'Line' text field to '3'.
   Change the 'Item Type' to 'Run/Program Data Description' then click 'Change'. Once the 'Select Data Item' window opens expand 'Load Arm Layout' and click 'Number of Load Arms'. Press OK twice.
    Expected Result: _There will be a Text Field on the view that says 'Number of Load Arms'._ *[PASS/FAIL]*

5. In the top left of the window click on the Circle button then click 'Save' or 'Save as...'  Give the file a valid name and location then click 'Save'
    Expected Result: _The file will save successfully to the file system._ *[PASS/FAIL]*

6. In your file system explorer navigate the the file location and verify that it exists.
    Expected Result: _The file will exist in the assigned location with the given name._ *[PASS/FAIL]*

AccuMate IV Report Configuration Created:

h4. B3: Loading Report Files

1. With the Report view still open from the previous test case, click the top left button for the drop down and select 'Save As...' and save the file with a different name.
    Expected Result: _The Report file will be saved under the new name as well as the old. AccuMate will have the new Report view open with the new name._ *[PASS/FAIL]*

2. In the top left click on the Circle button then click open.
    Expected Result: _AccuMate will have both the old and new Report views open._ *[PASS/FAIL]*

3. Navigate to the AccuLoad IV report file (.al4rep) with the old name (not the one you just saved) and select it, then click 'Open'.  Verify that the contents of each Report view are the same.
    Expected Result: _Both views contain the same content._ *[PASS/FAIL]*

AccuMate IV Report Configuration Created:

h4. B4: Uploading Empty Report File

1. Click the top left circle button then hover your mouse over 'New'.  Click on 'AccuMate Config File'.
    Expected Result: _An AccuMate Configurations file is created and displayed on the application._ *[PASS/FAIL]*

2. Click on 'Document Options' in the top ribbon.  Enter in the IP address of the target AccuLoad instance and OK the dialog.
    Expected Result: _The AccuMate will connect successfully to the target AccuLoad._ *[PASS/FAIL]*

3. Create a new empty Report file (.al4rep) by clicking the top left circle button, selecting "New->Report Configuration", and then saving the file as B4_empty.al4rep.  *[PASS/FAIL]*

4. Click on Upload File to AccuLoad.  Browse and select the empty Report file (.al4rep). Upload it to the  AccuLoad. Select the "User Configured Report 1 - Transaction Report" option and OK the dialog.
    Expected Result: _A popup warning with the text "No entries defined. Nothing to upload." will be displayed._ *[PASS/FAIL]*

h4. B5: Uploading Report Files - Transaction Report

1. Start the AccuMate Application.

2. Click the top left circle button then hover your mouse over 'New'.  Click on 'AccuMate Config File'.
    Expected Result: _The application will open to a blank view. The application will display a new configuration._ *[PASS/FAIL]*

3. Click on 'Document Options' in the top ribbon.  Enter in the IP address of the target AccuLoad instance and OK the dialog.
    Expected Result: _The AccuMate will connect successfully to the target AccuLoad._ *[PASS/FAIL]*

4. Click on Upload File to AccuLoad.
    Expected Result: _The "AccuMate File Transfer" window will appear._ *[PASS/FAIL]*

5. Click "Browse..." and open the Report File you want to upload (.al4rep) then click "Start". When the "Select Report" dialog appears, select "User Configured Report 1 - Transaction Report" and OK the dialog. Then wait for the upload to finish.
    Expected Result: _The upload will complete successfully._ *[PASS/FAIL]*

AccuMate IV Report File Used:

h4. B6: Downloading Report Files - Transaction Report

1. Start the AccuMate Application.
    Expected Result: _The application will open to a blank view._ *[PASS/FAIL]*

2. Click the top left circle button then hover your mouse over 'New'.
    Expected Result: _The options for new files will appear, 'AccuMate Config File' being one of them._ *[PASS/FAIL]*

3. Click on 'AccuMate Config File'.
    Expected Result: _The application will display a new AccuMate Config File._ *[PASS/FAIL]*

4. Click on 'Document Options' in the top ribbon.  Enter in the IP address of the target AccuLoad instance and OK the dialog.
    Expected Result: _The AccuMate will connect successfully to the target AccuLoad._ *[PASS/FAIL]*

5. Click on 'Download File From AccuLoad' in the top ribbon and select "Report Files". Select "User Configured Report 1 - Transaction report". OK the dialog.
    Expected Result: _The download progress dialog will appear._ *[PASS/FAIL]*

6. Choose a valid filename/location and Start the download.
    Expected Result: _The download will complete successfully. _ *[PASS/FAIL]*

7. Verify that this matches the Report File that was uploaded to the
   AccuLoad by opening the downloaded and uploaded file side by side in AccuMate to compare them.
    Expected Result: _The report files will be the same._ *[FAIL]*

_Note:  Files do not match...downloaded file is missing data....see ticket #3861
AccuMate IV Report File downloaded:
compared to previously uploaded file:

h4. B7: Uploading Report Files - Batch Report

1. Start the AccuMate Application.
    Expected Result: _The application will open to a blank view._ *[PASS/FAIL]*

2. Click the top left circle button then hover your mouse over 'New'.
    Expected Result: _The options for new files will appear, 'AccuMate Config File' being one of them._ *[PASS/FAIL]*

3. Click on 'AccuMate Config File'.
    Expected Result: _The application will display a new AccuMate Config File._ *[PASS/FAIL]*

4. Click on 'Document Options' in the top ribbon.  Enter in the IP address of the target AccuLoad instance and OK the dialog.
    Expected Result: _The AccuMate will connect successfully to the target AccuLoad._ *[PASS/FAIL]*

5. Click on Upload File to AccuLoad.
    Expected Result: _The "AccuMate File Transfer" window will appear._ *[PASS/FAIL]*

6. Click "Browse..." and open the Report File you want to upload (.al4rep) then click "Start". When the "Select Report" dialog appears, select "User Configured Report 1 - Batch Detail" and OK the dialog. Then wait for the upload to finish.
    Expected Result: _The upload will complete successfully._ *[PASS/FAIL]*

h4. B8: Downloading Report Files - Batch Report

1. Start the AccuMate Application.
    Expected Result: _The application will open to a blank view._ *[PASS/]*

2. Click the top left circle button then hover your mouse over 'New'.
    Expected Result: _The options for new files will appear, 'AccuMate Config File' being one of them._ *[PASS/FAIL]*

3. Click on 'AccuMate Config File'.
    Expected Result: _The application will display a new AccuMate Config File._ *[PASS/FAIL]*

4. Click on 'Document Options' in the top ribbon.  Enter in the IP address of the target AccuLoad instance and OK the dialog.
    Expected Result: _The AccuMate will connect successfully to the target AccuLoad._ *[PASS/FAIL]*

5. Click on 'Download File From AccuLoad' and select "Report Files". Select "User Configured Report 1 - Batch Detail". OK the dialog.
    Expected Result: _The download progress dialog will appear._ *[PASS/FAIL]*

6. Choose a valid filename/location and Start the download.
    Expected Result: _The download will complete successfully. _ *[PASS/FAIL]*

7. Verify that this matches the Report File that was uploaded to the AccuLoad by opening the downloaded and uploaded file side by side in AccuMate to compare them.
    Expected Result: _The report files will be the same._ *[FAIL]*
   _Note:  Files do not match...downloaded file is missing data....see ticket #3861
   AccuMate IV Report File downloaded:
   compared to previously uploaded file:

h4. B8: Downloading Report Files - Batch Report

1. Start the AccuMate Application.
    Expected Result: _The application will open to a blank view._ *[PASS/]*

2. Click the top left circle button then hover your mouse over 'New'.
    Expected Result: _The options for new files will appear, 'AccuMate Config File' being one of them._ *[PASS/FAIL]*

3. Click on 'AccuMate Config File'.
    Expected Result: _The application will display a new AccuMate Config File._ *[PASS/FAIL]*

4. Click on 'Document Options' in the top ribbon.  Enter in the IP address of the target AccuLoad instance and OK the dialog.
    Expected Result: _The AccuMate will connect successfully to the target AccuLoad._ *[PASS/FAIL]*

5. Click on 'Download File From AccuLoad' and select "Report Files". Select "User Configured Report 1 - Batch Detail". OK the dialog.
    Expected Result: _The download progress dialog will appear._ *[PASS/FAIL]*

6. Choose a valid filename/location and Start the download.
    Expected Result: _The download will complete successfully. _ *[PASS/FAIL]*

7. Verify that this matches the Report File that was uploaded to the AccuLoad by opening the downloaded and uploaded file side by side in AccuMate to compare them.
    Expected Result: _The report files will be the same._ *[FAIL]*
   _Note:  Files do not match...downloaded file is missing data....see ticket #3861
   AccuMate IV Report File downloaded:
   compared to previously uploaded file:

h4. B9: Uploading Report Files - Prove Report

1. Start the AccuMate Application.
    Expected Result: _The application will open to a blank view._ *[PASS/FAIL]*

2. Click the top left circle button then hover your mouse over 'New'.
    Expected Result: _The options for new files will appear, 'AccuMate Config File' being one of them._ *[PASS/FAIL]*

3. Click on 'AccuMate Config File'.
    Expected Result: _The application will display a new AccuMate Config File._ *[PASS/FAIL]*

4. Click on 'Document Options' in the top ribbon.  Enter in the IP address of the target AccuLoad instance and OK the dialog.
    Expected Result: _The AccuMate will connect successfully to the target AccuLoad._ *[PASS/FAIL]*

5. Click on Upload File to AccuLoad.
    Expected Result: _The "AccuMate File Transfer" window will appear._ *[PASS/FAIL]*

6. Click "Browse..." and open the Report File you want to upload (.al4rep) then click "Start". When the "Select Report" dialog appears, select "Prove Report" and OK the dialog. Then wait for the upload to finish.
    Expected Result: _The upload will complete successfully._ *[PASS/FAIL]*

AccuMate IV Report Config used:

h4. B10: Downloading Report Files - Prove Report

1. Start the AccuMate Application.
    Expected Result: _The application will open to a blank view._ *[PASS/FAIL]*

2. Click the top left circle button then hover your mouse over 'New'.
    Expected Result: _The options for new files will appear, 'AccuMate Config File' being one of them._ *[PASS/FAIL]*

3. Click on 'AccuMate Config File'.
    Expected Result: _The application will display a new AccuMate Config File._ *[PASS/FAIL]*

4. Click on 'Document Options' in the top ribbon.  Enter in the IP address of the target AccuLoad instance and OK the dialog.
    Expected Result: _The AccuMate will connect successfully to the target AccuLoad._ *[PASS/FAIL]*

5. Click on "Download File From AccuLoad" and select "Report Files". Select "Prove report". OK the dialog.
    Expected Result: _The download progress dialog will appear._ *[PASS/FAIL]*

6. Choose a valid filename/location and Start the download.
    Expected Result: _The download will complete successfully. _ *[PASS/FAIL]*

7. Verify that this matches the Report File that was uploaded to the AccuLoad by opening the downloaded and uploaded file side by side in AccuMate to compare them.
    Expected Result: _The report files will be the same._ *[FAIL]*
   _Note:  Files do not match...downloaded file is missing data....see ticket #3861
   AccuMate IV Report File downloaded:
   compared to previously uploaded file:

h4. B11: Loading AM3 Report Files

1. Start the AccuMate IV application.
    Expected Result: _The application will open to a blank view._ *[PASS/FAIL]*

2. Click the "Open" option under the top left drop down menu.
    Expected Result: _The open file dialog will open._ *[PASS/FAIL]*

3. Select the desired AM3 Report File (.RPX) and click open. Verify that the report matches the expected output below.
    Expected Result: _The AM3 Report File will successfully load onto AM4 and matches the expected output._ *[PASS/FAIL]*

4. Save the AM3 Report File to an AM4 Report File (.al4rep) from either the "Save" or "Save as" option under the top left drop down menu.
    Expected Result: _The file will successfully save the the file system._ *[PASS/FAIL]*

5. Close the newly saved AM4 Report file and reopen the .al4rep file you
   just saved.
    Expected Result: _The Report File will successfully load onto AM4._ *[PASS/FAIL]*

6. Open up the saved AM3 Report file once more and compare the contents in the new file with the old file.
    Expected Result: _Both files will have the same data._ *[PASS/FAIL]*

AccuMate IV Report Configurations Created/Used:

h4. B12: Loading Early AM4 Report Files

1. With the AccuMate application displayed, go to the top left of the application and select the drop-down menu circle. Select the "Open" option.
    Expected Result: _A window to select the file to open is displayed._ *[PASS/FAIL]*

2. Navigate to the location of the early AM4 version Report file and open it
   into AccuMate.
    Expected Result: _The early AM4 file will open._ *[PASS/FAIL]*

3. Review the contents of the report and note any entries with no
   information.
    Expected Result: _The values for Alarms in Transactions will each be populated with <none>, signifying no information._ *[PASS/FAIL]*

4. Double-click on each <none> value and OK the Edit Item dialog that
   arises.
    Expected Result: _The <none> values will be overwritten with NNN..., signifying a placeholder for valid information._ *[PASS/FAIL]*

AccuMate IV Report Configs used/created:

h4. B13: Upload/Download Multiple Times

1. At the top of the application, select the "Upload file to AccuLoad" button.
    Expected Result: _The dialog to upload a file will be displayed._ *[PASS/FAIL]*

2. Select "Browse" and select one of the report files to upload to the AccuLoad. Click "Start". Select the "User Configured Report 1Transaction Report" option, then OK the dialog.
    Expected Result: _The file successfully uploads to AccuLoad._ *[PASS/FAIL]*

3. Beside the "Upload file to AccuLoad" button is the "Download file from AccuLoad" button; select it to bring up the download dialog window.
    Expected Result: _The Download file to AccuLoad dialog window is displayed._ *[PASS/FAIL]*

4. Select "Report Files" and OK the dialog. Then select "User Configured Report 1- Transaction Report" and OK that dialog as well. Select a location to save the file and "Start" the download.
    Expected Result: _The report file is downloaded into AccuMate._ *[PASS/FAIL]*

5. Verify that the file that was just downloaded is opened into AccuMate and has the same contents as the file that was previously uploaded.
    Expected Result: _The file that was downloaded matches the uploaded file._ *[PASS/FAIL]*

6. Repeat steps 1-5 again, but this time with a different report file. Verify that the 2nd report file can be uploaded and downloaded.
    Expected Result: _The file is successfully uploaded to the AccuLoad. The file is successfully downloaded from AccuLoad._ *[PASS/FAIL]*

h4. B14: No Report To Download

1. Select the "Download File From AccuLoad" button. Select "Report Files" and OK the dialog. Then select "User Configured Report 1 - Batch Detail". OK this dialog as well. Choose a valid save location for the file and begin the download. Verify that a warning popup is displayed, explaining that there is no information to pull from the AccuLoad.
    Expected Result: _A warning popup is displayed, notifying the user that there is no information to pull._ *[PASS/FAIL]*

2. Repeat this process for each of the report file types:
- User Configured Report 1 
- Transaction Report 
- User Configured Report 2 
- Batch Detail 
- User Configured Report 2 
- Transaction Report 
- Prove Report
  Verify all of the downloads result in a warning popup notifying the user there is no information to pull.
    Expected Result: _A warning popup is displayed for all report downloads._ *[PASS/FAIL]*

NOTE:  The AccuLoad IV will need to have all *.CFG files in _/media/data/database_ removed prior to performing this test...as after previous (B1-B13) will have configurable reports available in the AccuLoad.

h4. B15: Creating UserText Items

1. Start the AccuMate Application.  The application will open to a blank view.

2. Click the top left circle button then hover your mouse over 'New'.
    Expected Result: _The options for new files will appear, 'Report Configuration' being one of them._ *[PASS/FAIL]*

3. Click on 'Report Configuration'.
    Expected Result: _The application will display a new Report Configuration._ *[PASS/FAIL]*

4. Right click on the canvas and click Insert New Here...
    Expected Result: _The application will open a dialog to prompt the insertion of a new item. _ *[PASS/FAIL]*

5. Change the "Item Value" text input to "Testing User Text" and OK the dialog.
    Expected Result: _The new item will be displayed with the chosen user text._ *[PASS/FAIL]*

h4. B16: Creating Value/Description Items

1. Start the AccuMate Application.
    Expected Result: _The application will open to a blank view._ *[PASS/FAIL]*

2. Click the top left circle button then hover your mouse over 'New'.
   The options for new files will appear, 'Report Configuration' being one of them.

3. Click on 'Report Configuration'.
    Expected Result: _The application will display a new Report Configuration._ *[PASS/FAIL]*

4. Right click on the top left corner of the canvas and click "Insert New
   Here..."
    Expected Result: _The application will open a dialog to prompt the insertion of a new item._ *[PASS/FAIL]*

5. Change Item Type to "Run/Program Data Description".
    Expected Result: _Data Register and Item Value will change values to "<none>"._ *[PASS/FAIL]*

6. Change the Data Register value to "Load Arm Layout"->"Number of Load
   Arms" and OK the dialog.
    Expected Result: _The new item will display the text "Number of Load Arms"._ *[PASS/]*

7. Repeat steps 3-5 one row beneath the previous item and with the Type
   "Run/Program Data Value".
    Expected Result: _The new item will display the number 6._ *[PASS/FAIL]*

h4. B17: Creating Value/Description Items with Offsets

1. Start the AccuMate Application.
    Expected Result: _The application will open to a blank view._ *[PASS/FAIL]*

2. Click the top left circle button then hover your mouse over 'New'.  Click on 'Report Configuration'.
    Expected Result: _The application will display a new Report Configuration._ *[PASS/FAIL]*

3. Right click on the canvas and click Insert New Here... 
    Expected Result: _The application will open a dialog to prompt the insertion of a new item. _ *[PASS/FAIL]*

4. Change Item Type to "Run/Program Data Description".
    Expected Result: _Data Register and Item Value will change values to "<none>"._ *[PASS/FAIL]*

5. Click the 'Change' button to change the Data Register value to "Pulse Input Config"->"Pulse Input Tag" and under Offset set the value at 1. OK this dialog.
    Expected Result: _The Data Register text field will read "Pulse Input Tag (1)"._ *[PASS/FAIL]*

6. OK this dialog. 
    Expected Result: _The new item will display the text "Pulse Input Tag"._ *[PASS/FAIL]*

7. Double-click on the item to re-open the item editor dialog. 
    Expected Result: _"Pulse Input Config"->"Pulse Input Tag" will still be selected, with an offset of 1._ *[PASS/FAIL]*

8. Click 'Change' to open the change window.
    Expected Result: _The item editor dialog will reappear._ *[PASS/FAIL]*

9. Change the offset to the max value (14) and OK the dialog.
    Expected Result: _The Data Register will read "Pulse Input Tag (14)"._ *[PASS/FAIL]*

10. OK this dialog. 
    Expected Result: _The new item will continue to display the text "Pulse Input Tag"._ *[PASS/FAIL]*

11. Double-click on the item to re-open the item editor dialog. 
    Expected Result: _The item editor dialog will reappear._ *[PASS/FAIL]*

12. Click 'Change' to open the change window.
    Expected Result: _"Pulse Input Config"->"Pulse Input Tag" will still be selected, with an offset of 14._ *[PASS/FAIL]*

h4. B18: Changing the Format of Report Items

1. Start the AccuMate Application.
    Expected Result: _The application will open to a blank view._ *[PASS/FAIL]*

2. Open a new Report config file. (Select top-left circle button -> "New" -> "Report Configuration")
    Expected Result: _The application will display the new Report configuration._ *[PASS/FAIL]*

3. Right click on the canvas and click "Insert New Here..." 
    Expected Result: _The application will open a dialog to prompt the insertion of a new item.  *[PASS/FAIL]*

4. Change the Item Type element to "Run/Program Data Description".
    Expected Result: _Data Register and Item Value will change values to "<none>"._ *[PASS/FAIL]*

5. Select "Change" and navigate to "Load Arm Layout"->"Number of Load Arms". Then OK the dialog.
    Expected Result: _The new item will display the text "Number of Load Arms"._ *[PASS/FAIL]*

6. Click the "Advanced..." button and open the Advanced Report Item
   Options dialog.
    Expected Result: _The Advanced dialog will appear, and the format will be "%s"._ *[PASS/FAIL]*

7. Change the format to "%10.10s" (String of width 10) and OK the dialog.
    Expected Result: _The Edit Item dialog will now read "%10.10s" in the Format field, and the preview of the dialog will be adjusted formatted as specified._ *[PASS/FAIL]*

8. OK the dialog. 
    Expected Result: _The item will be displayed according to how it appeared in the preview of the Edit Item dialog._ *[PASS/FAIL]*

9. Double-click on the item to re-open the Edit Item dialog. 
    Expected Result: _The Edit Item dialog will be displayed and the format will appear as "%10.10s"._ *[PASS/FAIL]*

10. Open the Advanced Options Dialog again.
    Expected Result: _The Advanced dialog will appear, and the format will appear as "%10.10s"._ *[PASS/FAIL]*

h4. B19: Using Invalid Formats for String Report Items

1. Start the AccuMate Application.
    Expected Result: _The application will open to a blank view._ *[PASS/FAIL]*

2. Click the top left circle button then hover your mouse over 'New'.  Click on 'Report Configuration'.
    Expected Result: _The application will display a new Report Configuration._ *[PASS/FAIL]*

3. Right click on the canvas and click Insert New Here... 
    Expected Result: _The application will open a dialog to prompt the insertion of a new item._ *[PASS/FAIL]*

4. Change Item Type to "Run/Program Data Description".
    Expected Result: _Data Register and Item Value will change values to "<none>"._ *[PASS/FAIL]*

5. Change the Data Register value to "Load Arm Layout"->"Number of Load
   Arms", then press OK.
    Expected Result: _The new item will display the text "Number of Load Arms"._ *[PASS/FAIL]*

6. Click the "Advanced..." button and open the Advanced Report Item
   Options dialog.
    Expected Result: _The Advanced dialog will appear, and the format will be "%s"._ *[PASS/FAIL]*

7. Change the format to "%d" (integer) and OK the dialog.
    Expected Result: _The Advanced dialog will throw a warning that the user-supplied format is invalid because it is of the wrong type for this value._ *[PASS/FAIL]*

h4. B20: Moving Items

1. Start the AccuMate Application.
    Expected Result: _The application will open to a blank view._ *[PASS/FAIL]*

2. Open a new Report config file.
    Expected Result: _The application will display the new Report configuration._ *[PASS/FAIL]*

3. Right click on the canvas and click Insert New Here... 
    Expected Result: _The application will open a dialog to prompt the insertion of a new item._ *[PASS/FAIL]*

4. OK the dialog. 
    Expected Result: _The item will be displayed in its default form on the canvas._ *[PASS/FAIL]*

5. Drag and drop the item to a new valid location on the canvas.
    Expected Result: _A preview of the item will follow the cursor and the item will move to the new location indicated._ *[PASS/FAIL]*

h4. B21: Moving Items over other Items

1. Start the AccuMate Application.
    Expected Result: _The application will open to a blank view._ *[PASS/FAIL]*

2. Click the top left circle button then hover your mouse over 'New'.  Click on 'Report Configuration'.
    Expected Result: _The application will display a new Report Configuration._ *[PASS/FAIL]*

3. Right click on the canvas and click Insert New Here... 
    Expected Result: _The application will open a dialog to prompt the insertion of a new item._ *[PASS/FAIL]*

4. OK the dialog. 
    Expected Result: _The item will be displayed in its default form on the canvas._ *[PASS/FAIL]*

5. Repeat steps 3-4 one row beneath the previous Report Item. 
    Expected Result: _Another Report Item will appear on the canvas in default form._ *[PASS/FAIL]*

6. Drag one Report Item over the other.
    Expected Result: _The report Item preview will vanish, and the dragged Report Item will be unable to be dropped._ *[PASS/FAIL]*

h4. B22: Copy/Paste Items

1. Start the AccuMate Application.
    Expected Result: _The application will open to a blank view. _ *[PASS/FAIL]*

2. Click the top left circle button then hover your mouse over 'New'.  Click on 'Report Configuration'.
    Expected Result: _The application will display a new Report Configuration._ *[PASS/FAIL]*

3. Right click on the canvas and click "Insert New Here..."
    Expected Result: _The application will open a dialog to prompt the insertion of a new item._ *[PASS/FAIL]*

4. OK the dialog.
    Expected Result: _The item will be displayed in its default form on the canvas._ *[PASS/FAIL]*

5. Right-click on the item and select "Copy". Right-click below the item and select "Paste Here".
    Expected Result: _A duplicate of the item will be placed at the new location._ *[PASS/FAIL]*

h4. B23: Copy/Paste Text as an Item

1. Start the AccuMate Application.
    Expected Result: _The application will open to a blank view._ *[PASS/FAIL]*
2. Click the top left circle button then hover your mouse over 'New'.  Click on 'Report Configuration'.
    Expected Result: _The application will display a new Report Configuration._ *[PASS/FAIL]*
3. Copy the text "User Testing Text" here and paste it into the Report canvas at a suitable location.
    Expected Result: _The application will generate a new Report Item with this text displayed. _ *[PASS/FAIL]*

h4. B24: Creating Items Out of Bounds

1. Start the AccuMate Application.
    Expected Result: _The application will open to a blank view._ *[PASS/FAIL]*
2. Open a new Report config file.
    Expected Result: _The application will display the new Report configuration._ *[PASS/FAIL]*
3. Right click on the canvas and click "Insert New Here..."
    Expected Result: _The application will open a dialog to prompt the insertion of a new item._ *[PASS/FAIL]*
4. Change the "Item Value" input text to 100 '-' characters and OK the dialog. 
    Expected Result: _The dialog will throw a warning saying that the item cannot be placed out of bounds._ *[PASS/FAIL]*

*Characters used for this report test*
----------------------------------------------------------------------------------------------------

h4. B25: Moving Items Out of Bounds

1. Start the AccuMate Application.
    Expected Result: _The application will open to a blank view. _ *[PASS/FAIL]*
2. Open a new Report config file.
    Expected Result: _The application will display the new Report configuration._ *[PASS/FAIL]*
3. Right click on the canvas and click "Insert New Here..." 
    Expected Result: _The application will open a dialog to prompt the insertion of a new item._ *[PASS/FAIL]*
4. OK the dialog. 
    Expected Result: _The item will be displayed in its default form on the canvas._ *[PASS/FAIL]*
5. Drag the item to the far right side of the canvas.
    Expected Result: _Once outside of the report area, the preview of the item will disappear and the item will be unable to be placed._ *[PASS/FAIL]*

h4. B26: Changing Document Size

1. Start the AccuMate Application.
    Expected Result: _The application will open to a blank view._ *[PASS/FAIL]*
2. Open a new Report config file.
    Expected Result: _The application will display the new Report configuration._ *[PASS/FAIL]*
3. Open Document Options.
    Expected Result: _The Report Editor Document Options dialog will open, prompting for various changes to document attribute._ *[PASS/FAIL]*
4. Change the page size to custom: 100 x 100. OK the dialog.
    Expected Result: _The report will resize to 100 x 100._ *[PASS/FAIL]*
5. Insert a New Element by clicking the "Insert" button. Change the "Item Value" input value to '-' and the location to 100 x 100 (Line: 100 Column: 100). OK the dialog.
    Expected Result: _The item will be created and placed at that location since it is now a valid part of the canvas._ *[PASS/FAIL]*

_NOTE:  Ticket #3644 references an issue where the item properties window will not place the "-" at 100x100, however it can be manually dragged and placed to that location using the cursor._

*Report Configuration created for this test:*

h4. B27: Changing Document Size - Items Out of Bounds

1. With the previous configuration (100x100 sized report config from test B26), open Document Options.
    Expected Result: _The Report Editor Document Options dialog will open, prompting for various changes to document attribute._ *[PASS/FAIL]*
2. Change the page size to custom: 50 x 50. OK the dialog. (Make sure there is an item outside the 50x50 canvas range)
    Expected Result: _The dialog will throw a warning that the current document size will not print current report items._ *[PASS/FAIL]*

h4. B28: Changing Number of Pages in a Document

1. Start the AccuMate Application.
    Expected Result: _The application will open to a blank view._ *[PASS/FAIL]*
2. Open a new Report config file.
    Expected Result: _The application will display the new Report configuration._ *[PASS/FAIL]*
3. Open Document Options.
    Expected Result: _The Report Editor Document Options dialog will open, prompting for various changes to document attribute._ *[PASS/FAIL]*
4. Change the number of pages to 2. OK the dialog.
    Expected Result: _The report will resize to 120 x 80._ *[PASS/FAIL]*
5. Insert a New Element by clicking the "Insert" button. Change the "Input Text" value to '-' and the location to 120 x 80. OK the dialog.
    Expected Result: _The item will be created and placed at that location since it is now a valid part of the canvas._ *[PASS/FAIL]*

*Report Configuration created:*

h4. C1: Creating New Translation Files

1. Start the Accumate Application.
    Expected Result: _The application will open to a blank view. _ *[PASS/FAIL]*
2. Click the top left circle button then hover your mouse over 'New'.
    Expected Result: _The options for new files will appear, 'Translation' being one of them._ *[PASS/FAIL]*
3. Click on 'Translation'.
    Expected Result: _The application will display a new Translation view._ *[PASS/FAIL]*

h4. C2: Saving Translation Files

1. Double click on one of the lines then enter in a value to the 'New Text' text area in the window that appears. Click OK. Repeat this step 2 more times for a total of 3 entries.
    Expected Result: _The Translation column will contain the new values._ *[PASS/FAIL]*
2. Click the top left circle button then click 'Save' and enter a valid filename The file will successfully be saved to the file system with the supplied name and location.
    Expected Result: _Verify that the file has been successfully saved in the file system._ *[PASS/FAIL]*

*Translation File created:*

h4. C3: Loading Translation Files

1. With the Translation view still open from the previous test case C2, click the top left button for the drop down and select 'Save As...' and save the file with a different name.
    Expected Result: _The Translation file will be saved under the new name as well as the old. AccuMate will have the new Translation view open with the new name._ *[PASS/FAIL]*

2. Click the top left button for the drop down and select 'Open', then open the old file.
    Expected Result: _AccuMate will have both the old and new Translation views open. _ *[PASS/FAIL]*

3. Verify that the contents of each Translation view are the same.
    Expected Result: _Both views contain the same content._ *[PASS/FAIL]*

*Translation file created:*

h4. C4: Uploading Translation Files

1. Start the AccuMate Application.
    Expected Result: _The application will open to a blank view._ *[PASS/FAIL]*
2. Click the top left circle button then hover your mouse over 'New'. Click on 'AccuMate Config File'.
    Expected Result: _The application will display a new configuration._ *[PASS/FAIL]*
3. Open Document Options and enter in the IP address of the target AccuLoad instance and OK the dialog.
    Expected Result: _The AccuMate will connect successfully to the target AccuLoad._ *[PASS/FAIL]*
4. Click on Upload File to AccuLoad.
    Expected Result: _The "AccuMate File Transfer" window will appear._ *[PASS/FAIL]*
5. Click "Browse..." and open the Translation File you want to upload (.al4lang) then click "Start" and wait for the upload to finish.
    Expected Result: _The upload will complete successfully._ *[PASS/FAIL]*

h4. C5: Downloading Translation Files

1. Start the AccuMate Application.
    Expected Result: _The application will open to a blank view._ *[PASS/FAIL]*

2. Click the top left circle button then hover your mouse over 'New'. Click on 'AccuMate Config File'.
    Expected Result: _The application will display a new configuration._ *[PASS/FAIL]*

3. Open Document Options and enter in the IP address of the target AccuLoad instance and OK the dialog.
    Expected Result: _The AccuMate will connect successfully to the target AccuLoad._ *[PASS/FAIL]*

4. Click on Download File From AccuLoad and select Translations File. OK the dialog.
    Expected Result: _The download progress dialog will appear._ *[PASS/FAIL]*

5. Choose a valid filename/location and start the download.
    Expected Result: _The download will complete successfully._ *[PASS/FAIL]*

6. Open an SSH or SCP client and connect to the AccuLoad (User: Root Password: None).
    Expected Result: _The AccuLoad will connect and navigate to the Root user's home directory._ *[PASS/FAIL]*

7. Navigate to /ftp/.  The AccuLoad will display the directory /ftp/ and files translation_ file.txt and .command (Note the .command file may be hidden).

8. Download the translation_ file.txt file and compare it to the Translation File generated by AccuMate in step 5. Compare the files either by using AccuMate to open them both (you may need to change the file extension) or by computing a checksum (WinMD5 is a good program to use for this).
    Expected Result: _These files will be identical (same in AccuMate or same checksum)._ *[PASS/FAIL]*

*Translation Files:*

h4. C6: No Translation File To Download
_NOTE:  This test requires a Factory Default initialization in order to ensure there's no translation files present on the AccuLoad from previous tests._

1. Select the "Download File From AccuLoad" button. Select "Translation File" and OK the dialog. Choose a valid save location for the file and begin the download. Verify that a warning popup is displayed, explaining that there is no information to pull from the AccuLoad.
    Expected Result: _A warning popup is displayed, notifying the user that there is no information to pull._ *[PASS/FAIL]*

h4. C7: Loading AM3 Translation Files

1. Start the AccuMate application.
    Expected Result: _The application will open to a blank view._ *[PASS/FAIL]*

2. Click the "Open" option under the top left drop down menu.
    Expected Result: _The open file dialog will open._ *[PASS/FAIL]*

3. Select the desired AM3 Translation File (.LGX) and click open. Verify that the translations from the AM3 file transferred over (see images below). 
    Expected Result: _The AM3 Translation File will successfully load onto AM4 and the translations transferred over._ *[PASS/FAIL]*

4. Save the AM3 Translation File to an AM4 Translation File (.al4lang) from either the "Save" or "Save as" option under the top left drop down menu.
    Expected Result: _The file will successfully save in the file system. _ *[PASS/FAIL]*

5. Close the newly saved AM4 Translation file and reopen the .al4lang file you just saved.
    Expected Result: _The Translation File will successfully load onto AM4._ *[PASS/FAIL]*

*Translation Files used/created during this test:*

h4. D1: Create New Driver Database Files

1. Start the Accumate Application.
    Expected Result: _The application will open to a blank view. _ *[PASS/FAIL]*
2. Click the top left circle button then hover your mouse over 'New'.
    Expected Result: _The options for new files will appear, 'Driver Database' being one of them._ *[PASS/FAIL]*
3. Click on 'Driver Database'.
    Expected Result: _The application will display a new Driver Database view._ *[PASS/FAIL]*

h4. D2: Creating Driver Database Entries

1. Start the Accumate Application.
    Expected Result: _The application will open to a blank view._ *[PASS/FAIL]*

2. Click the top left circle button then hover your mouse over 'New'. Click on 'Driver Database'.
    Expected Result: _The application will display the new Driver Database configuration._ *[PASS/FAIL]*

3. Double click on the topmost entry to insert information.
    Expected Result: _The Edit Database Record" dialog will appear to enter in driver information._ *[PASS/FAIL]*

4. Click on "< Enter in HID Format..."
    Expected Result: _A dialog will be presented to provide a formatted ID._ *[PASS/FAIL]*

5. Enter a valid ID as dictated by the bounds on each field and OK the dialog. 
    Expected Result: _The "Edit Database Record" dialog will convert the formatted ID to a single number._ *[PASS/FAIL]*

6. OK the dialog.

h4. D3: Editing a Driver Database Entry

1. Double-click on the entry created in D2.
    Expected Result: _The "Edit Database Record" dialog will appear, loaded with the current values of the entry._ *[PASS/FAIL]*

2. Change the Card Data to a new value using the HID Format tool.
    Expected Result: _The previous value will be replaced by a formatted ID number._ *[PASS/FAIL]*

3. Under PIN #, enter the value 777. For each of the Additional data fields, respectively, enter "1", "2", and "3". OK the dialog.
    Expected Result: _The entry will be modified, showing the new ID and values of all edited fields._ *[PASS/FAIL]*

4. Double-click the entry to re-open the "Edit Database Record" dialog.
    Expected Result: _The dialog will be populated with the appropriate values found on the view._ *[PASS/FAIL]*

h4. D4: Saving Driver Database Files

1. Double click on the first row of the Driver Database view.
    Expected Result: _The 'Edit Database Record' view will appear._ *[PASS/FAIL]*

2. Click '< Enter in HID Format', change the 'Card #' field to something unique and press OK on the window that appears.
    Expected Result: _The 'Raw Card Data' field will be populated._ *[PASS/FAIL]*

3. Enter data into the Field 1, Field 2, and Field 3 text areas then press OK.
    Expected Result: _The first row on the Driver Database view will be populated with the information previously input._ *[PASS/FAIL]*

4. Repeat steps 1-3 two more times for a total of 3 rows.

5. Click the top left circle button then click 'Save' and enter a valid filename The file will successfully be saved to the file system with the supplied name and location.  Then click save. Verify that the file has been successfully saved in the file system. *[PASS/FAIL]*

*Driver Database file created for this test:*

h4. D5: Loading Driver Database Files

1. With the Database driver view still open from the previous test case D4, click the top left button for the drop down and select 'Save As...' and save the file with a different name.
    Expected Result: _The Database driver file will be saved under the new name as well as the old. AccuMate will have the new Database driver view open with the new name._ *[PASS/FAIL]*

2. Click the top left button for the drop down and select 'Open', then open the old file.
    Expected Result: _AccuMate will have both the old and new Driver database views open. _ *[PASS/FAIL]*

3. Verify that the contents of each Driver database view are the same.
    Expected Result: _Both views contain the same content._ *[PASS/FAIL]*

*Driver Database files created/used in this test:*

h4. D6: Uploading Driver Database Files

1. Start the AccuMate Application.
    Expected Result: _The application will open to a blank view._ *[PASS/FAIL]*

2. Click the top left circle button then hover your mouse over 'New'. Click on 'AccuMate Config File'.
    Expected Result: _The application will display a new configuration._ *[PASS/FAIL]*

3. Open Document Options and enter in the IP address of the target
   AccuLoad instance and OK the dialog.
    Expected Result: _The AccuMate will connect successfully to the target AccuLoad._ *[PASS/FAIL]*

4. Click on Upload File to AccuLoad.

5. Click "Browse..." and open the Driver Database File you want to upload (.al4ddb) then click "Start" and wait for the upload to finish.
    Expected Result: _The upload will complete successfully._ *[PASS/FAIL]*

h4. D7: Downloading Driver Database Files

1. Start the AccuMate Application.
    Expected Result: _The application will open to a blank view._ *[PASS/FAIL]*

2. Click the top left circle button then hover your mouse over 'New'. Click on 'AccuMate Config File'.
    Expected Result: _The application will display a new configuration._ *[PASS/FAIL]*

3. Open Document Options and enter in the IP address of the target AccuLoad instance and OK the dialog.
    Expected Result: _The AccuMate will connect successfully to the target AccuLoad._ *[PASS/FAIL]*

4. Click on "Download File From AccuLoad" and select "Driver Database File". OK the dialog.
    Expected Result: _The download progress dialog will appear._ *[PASS/FAIL]*

5. Choose a valid filename/location and Start the download.

6. Open an SSH or SCP client and connect to the AccuLoad (User: Root Password: None).
    Expected Result: _The AccuLoad will connect and navigate to the Root user's home directory._ *[PASS/FAIL]*

7. Navigate to /ftp/.
    Expected Result: _The AccuLoad will display the directory /ftp/ and files driver.txt and .command (Note the .command file may be hidden)._ *[PASS/FAIL]*

8. Download the driver.txt file and compare it to the Driver Database File generated by AccuMate in step 5. Compare the files either by using AccuMate to open them both (you may need to change the file extension) or by computing a checksum (WinMD5 is a good program to use for this)
    Expected Result: _These files will be identical (same in AccuMate or same checksum)._ *[PASS/FAIL]*

*Driver Database Files:*

h4. D8: No Driver Database File To Download

1. Select the "Download File From AccuLoad" button. Select "Driver
   Database File" and OK the dialog. Choose a valid save location for the file and begin the download. Verify that a warning popup is displayed, explaining that there is no information to pull from the AccuLoad.
    Expected Result: _A warning popup is displayed, notifying the user that there is no information to pull._ *[FAIL]*

*_NOTE:  After a Factory Init to remove any residual configuration files/databases, a download of driver databases from the AccuLoad with no driver.txt present in the /ftp directory on the AccuLoad results in a blank database being created with the filename provided during the dialog process.  Also a driver.txt is created in the /ftp directly immediately after trying to download._*

h4. D9: Loading AM3 Driver Database Files

1. Start the AccuMate application.
    Expected Result: _The application will open to a blank view._ *[PASS/FAIL]*

2. Click the "Open" option under the top left drop down menu.
    Expected Result: _The open file dialog will open._ *[PASS/FAIL]*

3. Select the desired AM3 Database Driver File (.3DB) and click open. Verify that the Database driver matches the expected output.
    Expected Result: _The AM3 Database Driver File will successfully load onto AM4 and match the expected output._ *[PASS/FAIL]*

4. Save the AM3 Database Driver File to an AM4 Database Driver File (.al4ddb) from either the "Save" or "Save as" option under the top left drop down menu.
    Expected Result: _The file will successfully save the the file system._ *[PASS/FAIL]*

5. Close the newly saved AM4 Database Driver file and reopen the .al4ddb file you just saved.
    Expected Result: _The Database Driver File will successfully load onto AM4._ *[PASS/FAIL]*

*Files created/used for this test:*

h4. E1: Create New Equation Files

1. Start the Accumate Application.
    Expected Result: _The application will open to a blank view._ *[PASS/FAIL]*

2. Click the top left circle button then hover your mouse over 'New'.
    Expected Result: _The options for new files will appear, 'Equation Set' being one of them._ *[PASS/FAIL]*

3. Click on 'Equation Set'.
    Expected Result: _The application will display a new Equation Set view._ *[PASS/FAIL]*

h4. E2: Saving Equation Files

1. Under 'Edit Options' in the top ribbon, click 'Insert'.
    Expected Result: _A New Item text field will be placed on the equation set view and the 'Edit Equation Line' window will open._ *[PASS/FAIL]*

2. From the 'With the result in this line, set the following' select input choose 'User BOOLEAN register...' then enter '1' into the 'Use this expression to...' text area. Then click OK.  The first line of the equation set will be populated with USERBOOL1 = 1

3. Repeat steps 1 - 2, incrementing the User Bool register and expression value (2, then 3) for a total of 3 rows.
    Expected Result: _Three rows will exist in the equation view._ *[PASS/FAIL]*

4. Click the top left circle button then click 'Save' and enter a valid filename.  Then click save. Verify that the file has been successfully saved in the file system.
    Expected Result: _The file will successfully be saved to the file system with the supplied name and location._ *[PASS/FAIL]*

*Equation Files generated:*

h4. E3: Loading Equation Files

1. With the equation set view still open from the previous test case E2, click the top left button for the drop down and select 'Save As...' and save the file with a different name.
    Expected Result:  _The Equation set file will be saved under the new name as well as the old. AccuMate will have the new equation set view open with the new name._ *[PASS/FAIL]*

2. Click the top left button for the drop down and select 'Open', then open the old file. (Same image as above).

3. Verify that the contents of each equation set view are the same.
    Expected Result: _AccuMate will have both the old and new equation set views open. Both views contain the same content._ *[PASS/FAIL]*

*Equation Files created during this test:*

h4. E4: Uploading Equation Files

1. Start the AccuMate Application.
    Expected Result: _The application will open to a blank view._ *[PASS/FAIL]*

2. Click the top left circle button then hover your mouse over 'New'. Click on 'AccuMate Config File'.
    Expected Result: _The application will display a new configuration._ *[PASS/FAIL]*

3. Open Document Options and enter in the IP address of the target AccuLoad instance and OK the dialog.
    Expected Result: _The AccuMate will connect successfully to the target AccuLoad._ *[PASS/FAIL]*

4. Click on Upload File to AccuLoad.
    Expected Result: _The "AccuMate File Transfer" window will appear._ *[PASS/FAIL]*

5. Click "Browse..." and open the Equation File you want to upload (.al4equ)
    Expected Result: _The upload will complete successfully._ *[PASS/FAIL]*

h4. E5: Downloading Equation Files

1. Start the AccuMate Application.
    Expected Result: _The application will open to a blank view._ *[PASS/FAIL]*

2. Click the top left circle button then hover your mouse over 'New'. Click on 'AccuMate Config File'.
    Expected Result: _The application will display a new configuration._ *[PASS/FAIL]*

3. Open Document Options and enter in the IP address of the target AccuLoad instance and OK the dialog.
    Expected Result: _The AccuMate will connect successfully to the target AccuLoad._ *[PASS/FAIL]*

4. Click on Download File From AccuLoad and select Equations File. OK the dialog.
    Expected Result: _The download progress dialog will appear._ *[PASS/FAIL]*

5. Choose a valid filename/location and Start the download.

6. Compare this file to the equations file uploaded in test E4.
    Expected Result: _The equations between the two files will be identical_ *[PASS/FAIL]*

*File downloaded from AccuLoad during this test:*

h4. E6: No Equation File To Download

1. Select the "Download File From AccuLoad" button. Select "Equations File" and OK the dialog. Choose a valid save location for the file and begin the download. Verify that a warning popup is displayed, explaining that there is no information to pull from the AccuLoad.
    Expected Result: _A warning popup is displayed, notifying the user that there is no information to pull._ *[PASS/FAIL]*

_NOTE: Equation.cfg file must be deleted from /media/data/database, or a fresh install of AccuLoad image in order for this test to be performed properly._

h4. E7: Loading AM3 Equation Files

1. Start the AccuMate application.
    Expected Result: _The open file dialog will open._ *[PASS/FAIL]*

2. Click the "Open" option under the top left drop down menu.
    Expected Result: _The application will open to a blank view_ *[PASS/FAIL]*

3. Select the desired AM3 Equation Set File (.EQX) and click open. Verify that the equation set matches the expected output.
    Expected Result: _The AM3 Equation Set File will successfully load onto AM4 and matches the expected output._ *[PASS/FAIL]*

4. Save the AM3 Equation Set File to an AM4 Equation Set File (.al4equ)
   from either the "Save" or "Save as" option under the top left drop down menu.
    Expected Result: _The file will successfully save the the file system._ *[PASS/FAIL]*

5. Close the newly saved AM4 Equation Set file and reopen the .al4equ file
   you just saved.
    Expected Result: _The Equation Set File will successfully load onto AM4._ *[PASS/FAIL]*

*Equation File created/used for this test:*

h4. E8: Uploading Empty Equation File

1. Click the top left circle button then hover your mouse over 'New'.  Click on 'AccuMate Config File'.
    Expected Result: _An AccuMate Configurations file is created and displayed on the application._ *[PASS/FAIL]*
2. Click on 'Document Options' in the top ribbon.  Enter in the IP address of the target AccuLoad instance and OK the dialog.
    Expected Result: _The AccuMate will connect successfully to the target AccuLoad._ *[PASS/FAIL]*
3. Click on Upload File to AccuLoad.
4. Browse and select the empty equations file. Upload it to the AccuLoad.
    Expected Result: _A popup warning with the text "No entries defined. Nothing to upload." will be displayed._ *[PASS/FAIL]*

*Empty AccuLoad Equations File:*

h4. F1: Downloading Empty Transaction Log

1. Start the Accumate Application.
    Expected Result: _The application will open to a blank view._ *[PASS/FAIL]*

2. Click the top left circle button then hover your mouse over 'New'. Click on 'AccuMate Config File'.
    Expected Result: _The application will display a new configuration._ *[PASS/FAIL]*

3. Open Document Options and enter in the IP address of the target Accuload instance and OK the dialog.
    Expected Result: _The AccuMate will connect successfully to the target Accuload._ *[PASS/FAIL]*

4. Select the "Download File from AccuLoad" option in AccuMate. Select "Transaction Log" and OK the Dialog. Choose a valid name/location to save the file and start the download. Verify that a warning popup is displayed.
    Expected Result: _A warning popup is displayed notifying the user no information is available._ *[PASS/FAIL]*

h4. F2: Download Transaction Log (Small)

1. Start the AccuMate Application.
    Expected Result: _The application will open to a blank view._ *[PASS/FAIL]*

2. Click the top left circle button then hover your mouse over 'New'. Click on 'AccuMate Config File'.
    Expected Result: _The application will display a new configuration._ *[PASS/FAIL]*

3. Open Document Options and enter in the IP address of the target Accuload instance and OK the dialog.
    Expected Result: _The AccuMate will connect successfully to the target Accuload._ *[PASS/FAIL]*

4. Click on Download File From Accuload and select Transaction Log. OK the dialog.
    Expected Result: _The download progress dialog will appear._ *[PASS/FAIL]*

5. Choose a valid filename/location and Start the download.
    Expected Result: _The download will complete successfully._ *[PASS/FAIL]*

6. Open an SSH or SCP client and connect to the Accuload (User: Root Password: None).
    Expected Result: _The Accuload will connect and navigate to the Root user's home directory._ *[PASS/FAIL]*

7. Navigate to /ftp/.
    Expected Result: _The Accuload will display the directory /ftp/ and files transaction_log.txt and .command (Note the .command file may be hidden)._ *[PASS/FAIL]*

8. Download the transaction_log.txt file and compare it to the
   transaction_log.txt file generated by AccuMate. Compare the files by using a diff tool (such as Beyond Compare) or by computing a checksum (WinMD5 is a good program to use for this).
    Expected Result: _These files will be identical._ *[PASS/FAIL]*

*Transaction Logs created during this test:*

h4. F3: Download Transaction Log (Large)

1. Start the AccuMate Application.
    Expected Result: _The application will open to a blank view._ *[PASS/FAIL]*
2. Open a new config file.
    Expected Result: _The application will display a new configuration._ *[PASS/FAIL]*
3. Open Document Options and enter in the IP address of the target AccuLoad instance and OK the dialog.
    Expected Result: _The AccuMate will connect successfully to the target AccuLoad._ *[PASS/FAIL]*
4. Click on Download File From AccuLoad and select Transaction Log. OK the dialog.
    Expected Result: _The download progress dialog will appear._ *[PASS/FAIL]*
5. Choose a valid filename/location and Start the download. 
    Expected Result: _The download will complete successfully._ *[PASS/FAIL]*
6. Open an SSH or SCP client and connect to the AccuLoad (User: Root Password: None).
    Expected Result: _The AccuLoad will connect and navigate to the Root user's home directory._ *[PASS/FAIL]*
7. Navigate to /ftp/.
    Expected Result: _The AccuLoad will display the directory /ftp/ and files transaction_log.txt and .command (Note the .command file may be hidden)._ *[PASS/FAIL]*
8. Download the transaction_log.txt file and compare it to the transaction_log.txt file generated
    Expected Result: _These files will be identical._ *[PASS/FAIL]*

h4. F4: Download Event Log

1. Start the AccuMate Application.
    Expected Result: _The application will open to a blank view._ *[PASS/FAIL]*

2. Click the top left circle button then hover your mouse over 'New'. Click on 'AccuMate Config File'.
    Expected Result: _The application will display a new configuration._ *[PASS/FAIL]*

3. Open Document Options and enter in the IP address of the target AccuLoad instance and OK the dialog.
    Expected Result: _The AccuMate will connect successfully to the target AccuLoad._ *[PASS/FAIL]*

4. Click on Download File From AccuLoad and select Event Log. OK the dialog.
    Expected Result: _The download progress dialog will appear._ *[PASS/FAIL]*

5. Choose a valid filename/location and Start the download.

6. Open an SSH or SCP client and connect to the AccuLoad (User: Root Password: None).
    Expected Result: _The AccuLoad will connect and navigate to the Root user's home directory._ *[PASS/FAIL]*

7. Navigate to /ftp/.
    Expected Result: _The AccuLoad will display the directory /ftp/ and files event_log.txt and .command (Note the .command file may be hidden)._ *[PASS/FAIL]*

8. Download the event log file and compare it to the event log file generated by AccuMate. (Beyond Compare is a great tool to use for this)
    Expected Result: _These files will be identical._ *[PASS/FAIL]*

*Event Logs created during this test:*

h4. F5: Download Audit Trail Log

1. Start the AccuMate Application.
    Expected Result: _The application will open to a blank view._ *[PASS/FAIL]*

2. Click the top left circle button then hover your mouse over 'New'. Click on 'AccuMate Config File'.
    Expected Result: _The application will display a new configuration._ *[PASS/FAIL]*

3. Open Document Options and enter in the IP address of the target
   AccuLoad instance and OK the dialog.
    Expected Result: _The AccuMate will connect successfully to the target AccuLoad._ *[PASS/FAIL]*

4. Click on Download File From AccuLoad and select Audit Trail Log. OK the dialog.
    Expected Result: _The download progress dialog will appear._ *[PASS/FAIL]*

5. Choose a valid filename/location and Start the download.
    Expected Result: _The download will complete successfully._ *[PASS/FAIL]*

6. Open an SSH or SCP client and connect to the AccuLoad (User: Root Password: None).
    Expected Result: _The AccuLoad will connect and navigate to the Root user's home directory._ *[PASS/FAIL]*

7. Navigate to /ftp/.
   The AccuLoad will display the directory /ftp/ and files audit_log.txt and .command (Note the .command file may be hidden).

8. Download the audit_log.txt file and compare it to the audit_log.txt file generated by AccuMate. Compare the files either by using a diff tool (such as BeyondCompare) or by computing a checksum (WinMD5 is a good program to use for this)
    Expected Result: _These files will be identical._ *[PASS/FAIL]*

*Audit Log files created during this test:*

h4. F6: Upload/Download License Status File

1. Start the AccuMate Application.
    Expected Result: _The application will open to a blank view._ *[PASS/FAIL]*
2. Open a new config file.
    Expected Result: _The application will display a new configuration._ *[PASS/FAIL]*
3. Open Document Options and enter in the IP address of the target AccuLoad instance and OK the dialog.
    Expected Result: _The AccuMate will connect successfully to the target AccuLoad._ *[PASS/FAIL]*
4. Click on Upload File to AccuLoad.
    Expected Result: _The "AccuMate File Transfer" window will appear._ *[PASS/FAIL]*
5. Click "Browse..." and open the License File you want to upload, then click "Start" and wait for the upload to finish.
    Expected Result: _The upload will complete successfully._ *[PASS/FAIL]*
6. OK the Dialog then click Exit. Click "Download File From AccuLoad".  Select License Status file. OK the Dialog.
    Expected Result: _The download progress dialog will appear._ *[PASS/FAIL]*
7. Choose a valid filename/location and Start the download.
    Expected Result: _The download will complete successfully._ *[PASS/FAIL]*

License Files downloaded/created:

h4. F7: No License Status To Download

1. Select the "Download File From AccuLoad" button. Select "License Status File" and OK the dialog. Choose a valid save location for the file and begin the download. Verify that a warning popup is displayed, explaining that there is no information to pull from the AccuLoad.
    Expected Result: _A warning popup is displayed, notifying the user that there is no information to pull._ *[PASS/FAIL]*

*NOTE:* _The license dongle needs to be pulled from the AccuLoad and the "DA: Arm Not Licensed" alarm present for this test to be performed._

h4. F8: Update Accuload Firmware

1. Start the AccuMate Application.
    Expected Result: _The application will open to a blank view._ *[PASS/FAIL]*

2. Open a new config file.
    Expected Result: _The application will display a new configuration._ *[PASS/FAIL]*

3. Open Document Options and enter in the IP address of the target AccuLoad instance and OK the dialog.
    Expected Result: _The AccuMate will connect successfully to the target AccuLoad._ *[PASS/FAIL]*

4. Click on the Icon for Accumate in the top-left corner of the application and click "Firmware Update".
    Expected Result: _A dialog will appear requesting the location of the firmware file._ *[PASS/FAIL]*

5. Navigate to the location of the firmware file. OK the file dialog. Then select "Yes" to update the AccuLoad.
    Expected Result: _The firmware update will begin._ *[PASS/FAIL]*

6. Once the firmware update has completed, open the Accuload and check the firmware version currently installed.
    Expected Result: _The firmware version will now match that of the most recent version of Accuload._ *[PASS/FAIL]*

h4. F9: Printing DriverDB Files (One Page)

1. Navigate to the circle drop-down menu on the top left of the application
   and select "Open..." Select the saved DriverDB file and open it.
    Expected Result: _The DriverDB file is open on the AccuMate._ *[PASS/FAIL]*

2. Go back up to the circle drop-down menu on the top left of the application and select "Print".
    Expected Result: _The print window will appear._ *[PASS/FAIL]*

3. For the "Name" parameter, make sure the value is set to "Microsoft Print to PDF". OK the dialog. Choose a location and file name and save it. Verify
    Expected Result: _The PDF is saved to the specified directory._ *[PASS/FAIL]*

4. Open the PDF and verify that all of the information from the DriverDB file was successfully printed onto the PDF. (There should be no header values)
    Expected Result: _All of the information is successfully printed onto the PDF with no errors. _ *[PASS/FAIL]*

Files used/created during this test:

h4. F10: Printing DriverDB Files (Multiple Pages)

1. Navigate to the circle drop-down menu on the top left of the application and select "Open..." Select the saved DriverDB file and open it.
    Expected Result: _The DriverDB file is open on the AccuMate._ *[PASS/FAIL]*

2. Go back up to the circle drop-down menu on the top left of the application and select "Print".
    Expected Result: _The print window will appear._ *[PASS/FAIL]*

3. For the "Name" parameter, make sure the value is set to "Microsoft Print to PDF". OK the dialog. Choose a location and file name and save it. Verify that the file was saved.
    Expected Result: _The PDF is saved to the specified directory._ *[PASS/FAIL]*

4. Open the PDF and verify that all of the information from the DriverDB file was successfully printed onto the PDF. (There should be no header values) The file should be more than one page long.  The PDF is composed of multiple pages of entries.
    Expected Result: _All of the information is successfully printed onto the PDF with no errors._ *[PASS/FAIL]*

Files created/printed for this test:

h4. F11: Printing AccuMate Config Files

1. Navigate to the circle drop-down on the top left of the AccuMate application. Select "Open..." and open up a AccuMate Config file.
    Expected Result: _The AccuMate Config file is loaded into the application._ *[PASS/FAIL]*

2. Navigate to the circle drop-down on the top left of the AccuMate application. Select "Print".
    Expected Result: _A printing window is displayed._ *[PASS/FAIL]*

3. For the "Name" property, make sure the value is "Microsoft Print to PDF".  OK the dialog.
    Expected Result: _The "Save Print Output As" screen is displayed._ *[PASS/FAIL]*

4. Save the PDF to a valid location. Verify that the file exists at the chosen directory.

5. Open up the PDF and verify that there are around 200 pages of data.

6. "CTRL + F" to look for the words "Maximum Available Arms". Once found, check and verify that the "Maximum Available Arms" and "Pemex Option" elements have an ID (Number in the first column).
    Expected Result: _The PDF is successfully saved. The data has been printed successfully into the PDF. Both elements have an ID._ *[PASS/FAIL]*

7. Scroll a little bit until you find the "Security Input" elements (Still under the same section). Verify that each element in that section has an ID.
    Expected Result: _All of the "Security Input" elements have an ID._ *[PASS/FAIL]*

8. "CTRL + F" to look for the number "740", which should navigate the screen to the element with ID number 740 under "Communications". Verify that the ID is there.
    Expected Result: _The element has an ID._ *[PASS/FAIL]*

9. "CTRL + F" to look for the "Arm 2" element. When the screen navigates to "Arm 2 Directory", verify that the elements in this section have an ID. Check the values and verify that the element values in the PDF match the values in the AccuMate application. Also check and verify that there are no alignment issues.  (A value of "0 Manual" and other similar values are OK)
    Expected Result: _All of the elements have the correct values and there are no alignment/formatting issues. Actual Result**_ *[PASS/FAIL]*

10. Scroll down or search for the "Meter 2" directory. (This section is not too far from the previous step) Verify that the elements in this section have an ID. Also check and verify that there are no alignment issues. (A value of "0 Digital" and other similar values are OK)
    Expected Result: _All of the elements have the correct values and there are no alignment/formatting issues._ *[PASS/FAIL]*

Config File Printed:

h4. F12: Printing Equation Files (Multiple Pages)

1. On the top left of the application, select the circle and select the "Open..." option on the drop down menu.
    Expected Result: _The "Open" window will be displayed._ *[PASS/FAIL]*

2. Navigate to where the equation file is located and select it to be opened in AccuMate.
    Expected Result: _The equation file is loaded into AccuMate._ *[PASS/FAIL]*

3. Go back to the drop-down menu at the top left of the application and choose the "Print" option.
    Expected Result: _The "Print" window will be displayed._ *[PASS/FAIL]*

4. Select the "Microsoft Print to PDF" option for the "Name" element. Then OK the dialog.
    Expected Result: _The "Save Print Output As" window is displayed._ *[PASS/FAIL]*

5. Save the PDF with a valid file name and at a valid location. Verify that the file was saved.
    Expected Result: _The file is successfully saved at the target location._ *[PASS/FAIL]*

6. Open the PDF file with the printed equation file data. Verify that the PDF has the correct data and is correctly formatted. The PDF should be multiple pages.
    Expected Result: _The PDF has the correct data inside and does not have any formatting issues.  The PDF has multiple pages._ *[PASS/FAIL]*

PDF file created:

h4. F13: Printing Equation Files (One Page)

1. On the top left of the application, select the circle and select the "Open..." option on the drop down menu.
    Expected Result: _The "Open" window will be displayed._ *[PASS/FAIL]*

2. Navigate to where the equation file is located and select it to be opened in AccuMate.
    Expected Result: _The equation file is loaded into AccuMate._ *[PASS/FAIL]*

3. Go back to the drop-down menu at the top left of the application and choose the "Print" option.
    Expected Result: _The "Print" window will be displayed._ *[PASS/FAIL]*

4. Select the "Microsoft Print to PDF" option for the "Name" element. Then OK the dialog.
    Expected Result: _The "Save Print Output As" window is displayed._ *[PASS/FAIL]*

5. Save the PDF with a valid file name and at a valid location. Verify that the The file is successfully saved at the target location.
    Expected Result: _The PDF file was saved._ *[PASS/FAIL]*

6. Open the PDF file with the printed equation file data. Verify that the PDF has the correct data and is correctly formatted. The PDF should be only one page.
    Expected Result: _The PDF has the correct data inside and does not have any formatting issues._ *[PASS/FAIL]*

Files used/created for this test:

h4. F14: API Table Conversions From A3X to Al4

1. On the AccuMate 3 application: Expand the Arm -> Meter -> Product directories and select Temperature/Density. Change the API Table parameter value to one of the values listed.
    Expected Result: _The "API Table" has been changed. The Reference Density and Density Units have changed for C/Ethanol API Tables. There is a file saved for each API Table option._ *[PASS/FAIL]*

If the chosen API Table is a C Table or is Ethanol (11.3.4)
Change the Reference Density parameter value to 123.456 Change the Reference Density for C Tables values to 1.1 (For one of the C/Ethanol Tables, keep the Reference Density for C Tables set to 0. For another Table, fileave the Reference Density for C Tables value blank) Change the System -> Temperature/Density Density Units value to Lb/F3
Save the AM3 file to a place in the file system. Repeat this process for ALL API Table options

2. On the AccuMate 4 application:  Load one of the .a3x files into AccuMate 4. Expand the Arm -> Meter -> Product directories and select Temperature/Density. Verify that the API Table value is set to the correct API Table conversion. (Check "API Tables.txt" file for the mapping of each API Table)
   If the API Table value includes "API"
   Verify that the Reference Density Units value is equal to the correct unit (Check "API Tables.txt" file for the correct Units for the table)
    Expected Result: _Each AccuMate 3 API Table is correctly converted when loaded into AccuMate 4._ *[PASS/FAIL]*

If the chosen API Table included a C Table or was Ethanol (11.3.4):
If the Ref Density of C Tables in AM3 was set to a non-zero number
Verify the API Table value is correct. (Use the API Tables text file) Verify that the Reference Density is equal to 1.1 (Ref Density of C Tables in AM3) Verify that the Coe cient of Expansion is set to 123.456 (The Ref Density set in AM3) Verify that the Product Reference Density Units is equal to what the System Reference Density Units was on AM3.
If the Ref Density of C Tables in AM3 was set to Zero/Blank
Verify the API Table value is correct. (Use the API Tables text file) Verify that the Coe cient of Expansion is set to 123.456 (The Ref Density set in AM3)
REPEAT THIS PROCESS FOR EACH API TABLE FROM ACCUMATE 3 AND VERIFY THE CORRECT DATA IS CONVERTED OVER TO ACCUMATE 4

Files used/created:

h4. F15: Parameter Conversions from A3X - Configuration File

1. Creating the AccuMate III Configuration File
   In the AccuMate III configuration file, update the System Status Display parameter to Yes. (Directory: System -> General Purpose)
    Expected Result: _The System Status Display value is set to Yes._ *[PASS/FAIL]*

2. Update the Inhibit Auto Focus parameter to Yes in the AccuMate III configuration file. (Directory: System -> Communications)
    Expected Result: _The Inhibit Auto Focus parameter is updated to Yes. The AccuMate III config file is saved._ *[PASS/FAIL]*

3. Switch over to AccuMate for AccuLoad IV and open up the saved AccuMate III config file that was saved in the previous step.
    Expected Result: _AccuMate goes through the appropriate steps to convert the A3X file into the AL4 file.  There were no errors related to any of the updated parameters._ *[PASS/FAIL]*

4. Navigate to the System -> General Purpose directory on the left side list view and observe the parameters displayed. Look for the System Status Display parameter and double click it.
    Expected Result: _The System Status Display parameter has the correct parameter value indicator of 139._ *[PASS/FAIL]*

5. Navigate to the System -> Communications directory on the left side list view and observe the parameters displayed. Look for the Inhibit Auto Focus parameter and double click it.
    Expected Result: _The Inhibit Auto Focus parameter has the correct parameter value indicator of 734. The Inhibit Auto Focus value is set to Yes_ *[PASS/FAIL]*

6. Establish a connection to the AccuLoad by selecting the Document Options and entering in the IP address of the AccuLoad. Select the Pull All From AccuLoad button at the top of AccuMate and allow the AccuLoad's configuration to load in the data. Observe the Inhibit Auto Focus and System Status Display values.
    Expected Result: _The AccuMate successfully pulled the configuration from the AccuLoad. There were no errors displayed for the updated parameters. The Inhibit Auto Focus and System Status Display values are now set to No._ *[PASS/FAIL]*

7. Disconnect from the AccuLoad before continuing.  Update the Inhibit Auto Focus value to Yes in AccuMate. Keep the System Status Display value as No. Once completed, reconnect to the AccuLoad unit and select the Push Selected to AccuLoad button while highlighting the System directory. When completed, observe the values of both parameters on the AccuLoad.
    Expected Result: _There were no problems pushing the updated configuration. The Inhibit Auto Focus value is updated to Yes and the System Status Display is still set to No in Program Mode on the AccuLoad._ *[PASS/FAIL]*

8. While connected to the AccuLoad, update the Inhibit Auto Focus and System Status Display values to Yes and No a few times. Each time a change is made, switch over to AccuLoad and observe the values in Program Mode.
    Expected Result: _The parameters on AccuLoad are updated to the correct value when the change is made in AccuMate._ *[PASS/FAIL]*

AccuMate Files used:

h4. F16: Parameter Conversions from A3X - Report File

1. On AccuMate III, open up a new Report Configuration File. Right-click the canvas and insert 2 Run/Program Data Description Item Types:
* Inhibit Auto Focus (Data Register -> Change... -> System Configuration -> 734 Inhibit Auto Focus) 

* System Status Display (Data Register -> Change... -> System Configuration -> 139 System Status Display)
  Save the Report file to the file system.
    Expected Result: _The System Status Display and Inhibit Auto Focus items are displayed in the Report in AccuMate III. The correct description is observed when an item is chosen. The AccuMate III report is saved._ *[PASS/FAIL]*
2. Switch over to AccuMate IV and open up the AccuMate III RPX Report file saved in the previous step. Observe the items displayed. Also observe the location of the items in the Select Data Item window.
   The System Status Display and Inhibit Auto Focus items are shown in their expected locations. (Different Description values are OK)
   There are no Invalid Register items shown on either of the items.
    Expected Result: _The System Status Display and Inhibit Auto Focus items are available in the Select Item Data window._ *[PASS/FAIL]*

3. Save the Report file so it is now saved as an .al4rep file. Close out of the report and re-open it as the newly saved .al4rep file. Observe the contents.
    Expected Result: _There were no problems saving the Report file into an .al4rep file. Opening the newly saved .al4rep file did not change any of the contents._ *[PASS/FAIL]*

AccuMate Report files created during this test:

h4. F17: Parameter Conversions from A3X - Equations File

1. Equations File Conversion
   Open up a new Equations file in AccuMate III. Insert 2 new User Boolean Register into the Equations File (Edit -> Insert New -> "User BOOLEAN Register" from the first drop down list). Double click each USERBOOL item and update one register to System Configuration 734 Inhibit Auto Focus and the other to System Configuration 139 System Status Display 
   (Double Click Item -> @Register... -> System Configuration) Once completed, save the equations file to the file system.
    Expected Result: _There are 2 USERBOOL items in the equation file, one for System Configuration 734 Inhibit Auto Focus and the other for System Configuration 139 System Status Display. The correct register is observed when the register value is chosen. The AccuMate 3 Equations file (.EQX) is saved to the file system._ *[PASS/FAIL]*

2. Switch over to the AccuMate IV application and open the .EQX file that was just saved in the previous step. Observe the items shown in the opened equations file. Double click the items and verify the Registers can be found in the Select Data Item list.
    Expected Result: _Both the Inhibit Auto Focus and System Status Display values were successfully loaded into AccuMate IV. The register items can be found in the Select Data Item list in AccuMate IV._ *[PASS/FAIL]*

3. Save the AccuMate III Equations file as an AccuLoad IV Equations file.  Close and re-open the newly saved Equations file (.al4equ). Observe the contents.
    Expected Result: _The Equations file is saved as a .al4equ file. Opening the newly saved .al4equ file leaves the contents unchanged._ *[PASS/FAIL]*

AccuMate Equation Files created:

h4. G1: Installing new version of AccuMate can't create new config docs

1. With the older AccuMate application opened, try to install the latest
   AccuMate version. Verify that the installation will not occur until the AccuMate application is closed.
    Expected Result: _The opened AccuMate application caused the installation to halt._ *[PASS/FAIL]*

2. Close the application and install the latest AccuMate.
    Expected Result: _AccuMate is installed with no problems._ *[PASS/FAIL]*

3. Open up AccuMate and try to create a new configurations file. Verify that a config file is created in AccuMate.
    Expected Result: _AccuMate can create a config file._ *[PASS/FAIL]*

4. With AccuMate running, try to install the latest version of AccuMate again. Verify that a message pops up indicating the application is running.
    Expected Result: _The popup message is displayed during installation._ *[PASS/FAIL]*

5. With AccuMate running, try to uninstall AccuMate. Verify that a message pops up indicating the application is running.
    Expected Result: _The popup message is displayed during the uninstall._ *[PASS/FAIL]*

h4. G2: Terms & Conditions in the Installer

1. Download the installer
    Expected Result: _The installer runs on your local machine_ *[PASS/FAIL]*

2. Run the installer. Verify that, before the application installs, a License Agreement window appears.
    Expected Result: _Before the application installs a License Agreement window appears_ *[PASS/FAIL]*

h4. G3: Install AccuMate as normal user

1. Double-click the AccuMate installer and run through the installation process. When the installation completes: - Verify that AccuMate can be opened without any errors and the correct version number is displayed in the About section.
    Expected Result: _AccuMate installs correctly and can be run without any errors. The correct version is displayed in the About section._ *[PASS/FAIL]*

2. Start AccuMate from desktop icon 
    Expected Result: _AccuMate starts properly._ *[NA]*
   _NOTE: Desktop icon is unavailable currently due to needing admin rights for the user to install the desktop icon without error during setup._

3. Start AccuMate from start menu 
    Expected Result: _AccuMate starts properly._ *[PASS/FAIL]*

4. Double-click an AccuMate .al4 file 
    Expected Result: _AccuMate starts properly_ *[FAIL]*
   _NOTE: Ticket #3841 created for this error._

5. Uninstall AccuMate.
    Expected Result: _AccuMate is uninstalled._ *[PASS/FAIL]*

h4. G4: Install AccuMate as Admin for All users

1. Run the installer .exe as Administrator. Choose 'Install for All Users' during installation
    Expected Result: _The installation completes successfully_ *[PASS/FAIL]*

2. Start AccuMate from the desktop icon 
    Expected Result: _Accuload starts successfully._ *[PASS/FAIL]*

3. Start AccuMate from the start menu 
    Expected Result: _AccuMate starts successfully_ *[PASS/FAIL]*

4. Start AccuMate by double-clicking a .al4 file 
    Expected Result: _AccuMate starts successfully_ *[FAIL]*
   _NOTE: Ticket #3841 created for this error._

5. Uninstall AccuMate
    Expected Result: _AccuMate uninstalls successfully - does not appear in the Start Menu any longer_ *[PASS/FAIL]*

h4. G5: Install AccuMate as Admin for the current user

1. Run the installer .exe as Administrator. Choose 'Install for Current User' during installation
    Expected Result: _The installation completes successfully_ *[PASS/FAIL]*

2. Start AccuMate from a desktop icon 
    Expected Result: _AccuMate starts successfully._ *[PASS/FAIL]*

3. Start AccuMate from the start menu 
    Expected Result: _AccuMate starts successfully._ *[PASS/FAIL]*

4. Start AccuMate by double-clicking a .al4 file 
    Expected Result: _AccuMate starts successfully._ *[FAIL]*
   _NOTE: Ticket #3841 created for this error._

5. Uninstall AccuMate
    Expected Result: _AccuMate uninstalls successfully - does not appear in the Start Menu any longer_ *[PASS/FAIL]*

h4. H1: DY Help file matches the most recent release of the Smith Manual
_NOTE:  At the time of this test, the revisions to the Smith Manual to include the addition of 20 (for a total of 44) injectors for the additive expansion project have not yet been completed.  This test shall verify that the additions to the corresponding AccuMate Help File topics are updated to include 44 injectors in the responses where appropriate._

1. Start AccuMate from the Start Menu.
   Expected Result:  _AccuMate starts successfully._ *[PASS/FAIL]*

2. Open the AccuMate Help file by clicking the "?" in the upper right corner of the application.
   Expected Result:  _The AccuMate Help window opens to the "AccuMate for AccuLoad Help Index" start page._ *[PASS/FAIL]*

3. Navigate to the Dynamic Displays help topic via "Online Reference Manuals -> AccuLoad IV Command Reference Contents" & select "DY - Dynamic Displays" in the right pane.
   Expected Result:  _The DY - Dynamic Displays" topic is shown._ *[PASS/FAIL]*

4. Verify that the *Injector Dynamic Displays* section includes entries for Injectors 1-44 for the following items:
* Injector Current Pulse Rate
* Injector Programmed Pulse Rate
  Expected Result:  _Values are displayed as described above._  *[PASS/FAIL]*
5. Verify that the *Batch Dynamic Displays* section includes entries for injectors 1-44 for the following item:
* Additive Batch Volume
  Expected Result: _Values are displayed as described above._ *[PASS/FAIL]*
6. Verify that the *Transaction Dynamic Displays* section includes entries for injectors 1-44 for the following item:
* Additive Transaction Volume
  Expected Result: _Values are displayed as described above._ *[PASS/FAIL]*

h4. H2: EA Help file and 2-character codes matches the most recent release of the Smith Manual
_NOTE:  At the time of this test, the revisions to the Smith Manual to include the addition of 20 (for a total of 44) injectors for the additive expansion project have not yet been completed.  This test shall verify that the additions to the corresponding AccuMate Help File topics are updated to include 44 injectors in the responses where appropriate._

1. Verify that the EA command topic shows an addition for injectors 25-44 in the command code descriptions (see entry I2). *[PASS/FAIL]*

2. Verify that the EA I2 results listing includes entries for injectors 25-44.  *[PASS/FAIL]*

h4. H3 - H8:  Updated max values for Parameters
Provided Configuration/Equation/Report Files:

1. Start AccuMate from the desktop icon or Start menu.
   Expected Result: _AccuMate starts successfully._  *[PASS/FAIL]*

2. Open H3-H3.AL4 AccuMate config file and connect to the AccuLoad using Document Options.  
   NOTE:  Adjust the following System Directory -> Communications parameters in the AL4 file to match your AccuLoad under test prior to uploading the config file
* 735 - IP Address

* 736 - Netmask

* 737 - Gateway
  Expected Result:  _The configuration file is uploaded successfully, and the AccuLoad remains "ONLINE" with AccuMate._ *[PASS/FAIL]*
3. Connect to the AccuLoad and upload the provided configuration file using the "Push All to AccuLoad" button in the menu bar.  
   Expected Result:  The AL4 configuration is uploaded to the AccuLoad successfully.  *[PASS/FAIL]*

4. Using the Upload File to AccuLoad button, upload the following files:
* H3-H8.al4equ

* H3-H8.al4rep
  When prompted, select "User Configured Report 1 - Transaction Report" for the Report location.
  Expected Result:  _The Equation and Report files are uploaded successfully._ *[PASS/FAIL]*
5. Using putty, connect to the AccuLoad and navigate to the /dev/shm directory on the ALIV.

6. Run a small batch on Arm 1, end the transaction, and save a copy of /dev/shm/report that is generated as arm1.txt.   Verify that the report generated matches the parameters as set in the configuration file.  _NOTE: Some items on the report are arm/meter/product specific to the batch being run._  *[PASS/FAIL]*

7. Repeat step 6 for Arm 2 and Arm 3.  *[PASS/FAIL]*

8. On the AccuLoad screen, under Dynamic Displays -> Diagnostics -> Boolean Algebraic, that the values there match the parameter settings in the AL4 configuration file.
   Expected Result:  _The values displayed in the Boolean Registers (User Floats) match the parameter settings._  *[PASS/FAIL]*

h4. H9 - HMI B Failure parameter removed from Systems Directory Listing

1. Start AccuMate from the desktop icon or Start menu.
   Expected Result: Accuload starts successfully. *[PASS/FAIL]*

2. Create a new AccuMate Config File.

3. Verify that the HMI B Failure parameter (1615) is no longer displayed in the System Directory -> 600 - Default Alarms parameter list.  *[PASS/FAIL]*
