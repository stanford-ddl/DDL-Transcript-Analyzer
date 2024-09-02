# DDL Transcript Analyzer
The Stanford DDL Transcript Analyzer takes in raw transcripts from deliberations and performs argument analysis on them.

## Table of Contents
* [Usage](#usage)
* [Notes for Future Developers](#notes-for-future-developers)
* [Gallery](#gallery)

## Usage
1. Navigate to the folder this program was downloaded to <code>DDL-Transcript-Analyzer</code>.
2. Open the <code>data</code> folder.
3. Create folders for each session you would like to analyze. For example, <code>1</code> for Session 1.* If that folder already exists, please ensure it is empty.
4. Place your data of <code>.xlsx</code> or <code>.csv</code> files into their appropriate session folder.
5. Exit the <code>data</code> folder and return to the main <code>DDL-Transcript-Analyzer</code> folder.
6. Run <code>main.py</code> and follow the on-screen prompts. If the program ever errors, redo this step.
7. Return to the main <code>DDL-Transcript-Analyzer</code> folder.
8. Open the <code>results</code> folder.
9. The results can be found in subfolder identical in name to the data folders you created in Step 3.

*In the future, we hope to remove the need for subfolders to simplify ease of use: [Issue #36](https://github.com/stanford-ddl/DDL-Transcript-Analyzer/issues/36)


## Notes for Future Developers
Please run the following commands before beginning development to avoid leaking API Keys and mixing up transcripts:
* <code>git update-index --skip-worktree codebase/api_keys.py</code>
* <code>git update-index --skip-worktree codebase/\_\_pycache\_\_/api_keys.cpython-312.pyc</code>
* <code>git update-index --skip-worktree data/</code>
* <code>git update-index --skip-worktree codebase/processing/</code>
* <code>git update-index --skip-worktree results/</code>

## Gallery
<img width="495" alt="Image1-DDL_Transcript_Analyzer" src="https://github.com/user-attachments/assets/718a8a96-5ba5-4455-8bbe-639137e9dda1">
<img width="495" alt="Image2-DDL_Transcript_Analyzer" src="https://github.com/user-attachments/assets/81db9979-047f-4428-b4d2-950f751147b4">
<img width="495" alt="Image3-DDL_Transcript_Analyzer" src="https://github.com/user-attachments/assets/53ca5361-7e3d-47d3-96ad-86ab82f57201">
<img width="495" alt="Image4-DDL_Transcript_Analyzer" src="https://github.com/user-attachments/assets/51de531f-3a7c-4b6b-abc4-40cd45f45625">
