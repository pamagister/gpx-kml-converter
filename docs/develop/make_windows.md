# 🛠️ How to Use `make` on Windows

This guide explains how to install and use `make` on Windows, with three different options depending on your preference and environment.

---

## ✅ Option 1: Use `make` on Windows via Git Bash

Git Bash provides a Unix-like shell on Windows. However, it **does not include `make` by default**, so you must install it separately.

### 📦 Step-by-Step: Installing Git Bash

1. Download Git for Windows:  
   👉 https://gitforwindows.org

2. Install Git and ensure that **Git Bash** is included in the installation.

3. Open Git Bash in your project folder by right-clicking and selecting **"Git Bash Here"**.

4. Now follow **Option 3** (below) to install `make` inside Git Bash via MSYS2.

---

## ✅ Option 2: Install GNU Make via Chocolatey

This method allows you to use `make` directly in PowerShell or Command Prompt.

### Prerequisites

Before installing GNU Make via Chocolatey, ensure you have Chocolatey package manager installed on your Windows system.

**To check if Chocolatey is installed:**
Open PowerShell as Administrator and run:
```bash
choco --version
```

**If Chocolatey is not installed:**

1. Open PowerShell as Administrator
2. Run the following command to install Chocolatey:

    ```
    Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
    ```
   
3. Close and reopen PowerShell as Administrator

### Installing GNU Make

1. **Open PowerShell or Command Prompt as Administrator**

    Press `Win + X` and select "Windows PowerShell (Admin)" or "Command Prompt (Admin)"

2. **Install GNU Make using Chocolatey**

    ```
    choco install make
    ```

3. **Confirm the installation**

    When prompted, type `y` or `yes` to proceed with the installation.

4. **Verify the installation**

5. After installation completes, verify that `make` is available:

    ```
    make --version
    ```
   
    You should see output similar to:

    ```
    GNU Make 4.x.x
    Built for Windows32
    ```

### Usage

Once installed, you can use `make` commands directly in any PowerShell or Command Prompt window:

```bash
# Navigate to your project directory
cd path\to\your\project

# Run make commands
make
make build
make clean
```

### Troubleshooting

**If `make` command is not recognized:**
1. Close and reopen your terminal
2. Check if the installation path is in your system PATH environment variable
3. Try running `refreshenv` in PowerShell to refresh environment variables

**To uninstall:**
```bash
choco uninstall make
```


## ✅ Option 3: Manually Add `make` to Git Bash via MSYS2

MSYS2 provides a full Unix toolchain for Windows, including `make`.

### 📦 Step-by-Step: Installing `make` using MSYS2

1. Download MSYS2 from:

    👉 [https://www.msys2.org](https://www.msys2.org)

2. Install MSYS2 (default path: `C:\msys64`).

3. Open the **"MSYS2 MSYS"** terminal (not UCRT64 or MINGW64).

4. Update the package manager:

    ```bash
    pacman -Syu
    ```

    📝 If prompted, close the terminal and re-open it after updating.

5. Install `make`:

    ```bash
    pacman -S make
    ```

6. Verify installation:

    ```bash
    make --version
    ```

---

### ⚙️ Add `make` to System PATH (Optional but Recommended)

To use `make` in Git Bash (or any terminal), you must add it to your system's PATH:

1. Find the path to `make`, usually:

    ```
    C:\msys64\usr\bin
    ```

2. Open **System Properties → Environment Variables**.

3. Under **"User variables"** or **"System variables"**, find the `Path` variable and click **Edit**.

4. Add the path:

    ```
    C:\msys64\usr\bin
    ```

5. Click **OK** and restart Git Bash or your system.

6. Test in Git Bash:

    ```bash
    make --version
    ```

---

## ✅ Example Usage

Once `make` is installed, you can run:

```bash
make fmt
```

From within your project folder, assuming you have a `Makefile` with a `fmt` target.

---

## 📝 Alternative: Bash Script Instead of Makefile

If you prefer not to install `make`, create a simple Bash script:

**format.sh**

```bash
#!/bin/bash
isort python-template-project/
black -l 100 python-template-project/
black -l 100 tests/
```

Make it executable:

```bash
chmod +x format.sh
./format.sh
```

---

## 🔚 Summary

| Option     | Description                     | Difficulty |
| ---------- | ------------------------------- |------------|
| Git Bash   | Use `make` in Unix-like shell   | Easy       |
| Chocolatey | Use `make` in PowerShell or CMD | Medium     |
| MSYS2      | Full Unix toolchain for Windows | Easy       |

Choose the option that best fits your workflow!
