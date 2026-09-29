---
crate: crate.37DBA7ACBE3DBC2A
title: Building: The Librarian
---
### {{title}}
{{div:papers}}
# the build plan from sdk
Librarian is about cataloging information, like a frontmatter / meta data shelf.  
-
It should allow us to add lines and store ones we have used before. 
**Examples**: time_created, time_imported, author. 
-
Should be able to also add lore cards. 
**Examples** "Found in the Evernote Woods" "Recovered from the endless logyard" "Remembered before time remembered." or even "Ex Husband's girlfriend returned after missing this for years." or "Painting while the world fell apart."  
-
Lore cards will get shipped md files to go.inbox/librarian so they may then be tagged or further cataloged. 
{{/div}}
{{div:papers}}
# the layout
Librarian Pop out should keep its same color, but launch in the companion rail size 
2 Buttons are Present at the top. **Add Meta Data** and **Add Lore**
Each open a modal. 

**Add Meta Data**
This modal contains:
    a drop down list of "types".
        TYPES are things like: time, bool, input, textbox
        TYPE defines what type of form element will be provided
    a fill in box for "label". 
        LABEL should auto-suggest previous used labels for this type
        LABEL should allow new uses to be used/added to the auto-suggest bank.
    the form element required by the TYPE
User will select the requirements, and complete the form on screen. 
A cancel or confirm button will be provided.
--
This content should be stored on a metadata page for this page. This YAML page should contain neatly the data stored by the inserts, including the matching CRATE number to the document being librarian'd.

**Add Lore**
This modal contains:
    a CLASS input
        CLASS should auto-fill previously used classes but allow new additions
    a LORE TITLE input
        LORE TITLE will be used to name the file lore addition generates
    a LORE LINE input
        LORE LINE is a limited 255 character max insert about a LORE record on this item
    a LIBRARIAN TIME REFERENCE input
        LIBRARIAN TIME is an time input where any inserted time, whether unix or common form, converts to unix and stores on the lore as TPS REFERENCE. If none is entered, use the current datetime.
--
This content should be stored as single .md files per LORE insert, sent to the OFFICE of THE LIBRARIAN, into their INBOX. The filename should match the lore title, with a LOR_XX added to the end. *ie A_Strange_Day-LORE_302*
--
Contents of the LORE card sent should include the crate ID it was spawned from, that the librarian created it, and should include all of the information from the form insert. Additionally, the page should backlink to the crate it was created on as a wikilink.
{{/div}}
