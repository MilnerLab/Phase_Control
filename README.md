# Project Setup & Useful Commands

This repository contains.  
Below is a quick reference for setting up the environments and running the programs.

---

## 1. Virtual Environment

### 1.1 Creates / checks / activates environments

Use the provided PowerShell script:

```powershell
. .\setup_env.ps1
````

This script will:

* Creates both virtual environments (`.venv32` and `.venv64`) if they do not exist
* Activate the virtual environment
* Install / update the required packages
* Install / update the recommended extensions

### 1.2 Manually activate existing venv (if needed)

If you need to activate the environment manually:

```powershell
.\.venv32\Scripts\Activate.ps1
.\.venv64\Scripts\Activate.ps1
```

---

## 3. Running the Applications

All applications are started via Python’s module syntax from the repository root.


```powershell
python -m app
```

