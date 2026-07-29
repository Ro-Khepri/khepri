=XMind Readme=

==License==

XMind 3 is dual licensed under 2 open source licenses: the Eclipse Public License v1.0 (EPL), 
which is available at http://www.eclipse.org/legal/epl-v10.html , and the GNU Lesser General 
Public License v3 (LGPL), which is available at http://www.gnu.org/licenses/lgpl.html .

XMind Pro 3 SLA is available at http://www.xmind.net/pro/license.html


==Requirements==

	Hardware:
		A 800Mhz or greater processor.
		256M RAM or greater, recommend 512M or greater.
		100MB free disk space for downloaded file and installaltion.
		Internet connection for certain features (like Share) and XMind Pro.

	Windows Users:
		Windows 2000(SP4)/XP/2003/Vista 32-bit.
		Microsoft Word/Powerpoint for certain features (like Export).
		
	Mac Users:
		Mac OS X 10.4 and later.

		
	Linux Users
		GTK.
		Some features need lame(http://lame.sourceforge.net/).
		Only Sun JRE/OpenJDK/IBM JRE/BEA JRockit are supported. Don't use unsupported JVM.


==Installation==

	First, Download XMind from http://www.xmind.net/
	
	For downloading zip portable package, unzip it to a clean folder. Open this folder, 
	and launch XMind directly without installation.
		
	For Windows installer, double-click it and follow the onscreen instructions. 

	For Mac disk image, double-click it to open a Finder window including "XMind.app" 
	(Some download tool would open it automatically.) Drag the "XMind.app" into your 
	Applications folder to copy it to your hard driver. You can drag XMind again from 
	the Applications folder to your dock, if you want.

==Release Notes==
Change of Version 3.1.0

New Features:
1. Default theme
2. Brainstorming mode and countdown timer
3. Export to PDF (Map)
4. Search tool
5. Sort topics
6. Add local file as relative hyperlink 
7. Add your own dictionary into XMind
8. New online update system
9. Add context menu when editing notes
10. Double click to open XMind file on Mac OS

Bugs:
1. Fishbone:  If changing map's structure to fishbone, add summary to a topic, drag and add more topic into this summary, click print, the layout is chaos. When reopening this map, the layout will be chaos too.
2. Extract Theme: If we extract a theme(named theme 1), close and reopen xmind, then extract another theme(its name will be the theme 1 automatically,), change its name (like to be theme 2).Now when we reopen XMind, the theme 2 is lost.
3. Context Menu: Only in the first sheet of the first workbook,  select a topic and right-click mouse, you can see the full context menu(including markers, and structures).
4. Upload map: If we add some special theme or style to a map and upload it to http://share.xmind.net/, then download this map and open it, all special theme and style will disappear. 
5. Import XMind 2008 file: If the map has wallpaper, that wallpaper will lose after being imported. 
6. Import FreeMind 0.9: Some Freemind 0.9 files can not be right imported into XMind.
7. Extract style: Sometimes, your extracted style will disappear after re-launching XMind Pro.
Some other bugs fixed.

Improvements:
1. Based on Eclipse RCP 3.5
2. Improve spell checker
3. Improve "Find and Replace"
4. Improve notes editing
5. XMind Pro users can use XMind Pro offline
Some other improvements.

Change of Version 3.0.3

New Features:
1. Crash Recovery
2. Topic Text Alignment
3. Export to FreeMind Map
4. Zoom the map with "Ctrl+Scroll Mouse Wheel"
5. Find and Replace the content in Label, Relationship and Boundary, Summary, and Rich Text Notes.
6. Auto Hyperlink 
7. SpellChecker in Rich Text Notes
8. Enter into presentation mode by using command line: "xmind -p xxx.xmind"(Available in Windows).

Bugs:
1. After enabling "Restore last session" in preference dialog, and restarting XMind without closing file, that file will be labeled dirty to ask you to save it.
2. After deleting the hyperlink and clicking 'ok' in the hyperlink dialog, that hyperlink is still available in that topic.
3. Some other bugs 

Improvements:
1. Improve the Memory usage, esp. on Windows.
2. Improve the performance, such as the speed to save a map which has some big attachments
3.Some other improvements.

Change of Version 3.0.2

New Features:
1. Security
2. New Sheet from Topic
3. Hyperlink in Notes

Bugs:
1. Delete any a topic in drilled down map, XMind will be back to the orginal map.
2. If enabling the "Auto-save", sometimes, it will report auto-save error.
3. When positioning the topic which has been added summary, the summary will has wrong direction sometimes.
4. Selecting and Positioning multiple topics which have boundary together will bring chaos
5. The last two default styles in the style view are not available.
6. Add boundary to multiple main branches in fishbone, the layout will be chaos.
7. Pasting the multiple lines structural text into XMind has no effect.
8. If using mouse context menu to align topics, users may not use alignment feature again untill re-open the XMind.

Improvements:
1. Improve XMind speed 
2. Improve XMind performance and use less memory
3. Improve Fishbone layout
4. Importing FreeMind file performs better.
5. XMind can run better on Mac OS X 10.4 fluently.
6. Using personal markers in a map, and sharing with others, the markers sometimes can not been see.
7. Enhance Save Sheet as...

Change of version 3.0.1

New Features:
1. New Mind Map Structure: Clockwise and Anti Clockwise
2. Import XMind 2008 file.
3. Export to XMind 2008 file.
4. Map Shot:  User can set a path to save.
5. Hyperlink: Users can add Local File/Folder link, and topic link(in the same workbook) to a topic.
6. The personal markers in a map can be seen after opening the map in another computer.
7. New languages package including German, Japanese, Chinese(Simplified), Chinese(Traditional)
8. New relationship style: Zigzag.
9. New markers.

Bugs:
1. XMind can not run on PowerPC-based Mac OS X Tiger 10.4.
2. Print dialog will be freeze sometimes.
3. Marker, legend will become ugly if printing the map.
4. Extract a Theme, and apply to a map. This theme will be lost after reopening XMind and that file.
5. If users enable the Auto Save in XMind, open a new workbook and edit it, then leave XMind and do other work. After a while, there will be many "Save as" dialog.
6. Open the build-in browser, and open a website, now if there is no response after clicking a URL inside this website, closing this browser view will close XMind.
7. Spelling checker is in.
8. If users use XMind 3 to open an XMind 2008 file which has wallpaper, that wallpaper can not be read. 
Some other bugs fixed.

Improvement:
1. Can not open all XMind 2008 files directly.
2. Theme will be seen after uploading and exporting to images.
3. Users can drag an image into XMind as an individual topic.
4. Ctrl+Home will let users focus on Central topic and central topic be at center.
5. Users can change the Row order in Spreadsheet easily.
6. Importing Mind Manager file performs better.
7. Highlight the theme in current map in the theme view.
8. If a topic is near the left or right of editor, and now double clicking or F2 to edit it, the map will jump to let this topic be center of editor.
9. The Fishbone Chart has tapered line.
10. There is a print icon on toolbar.
11. New .deb package for Debian/Ubuntu Linux.
12. Open .xmind file directly from Share.xmind.net.
Some other improvements.
