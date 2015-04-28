MacPatchImporter for AutoPkg
=================

This processor adds the ability to upload AutoPkg packages to a MacPatch server.

#### MacPatchImporterProcessor
The MacPatchImporterProcessor recipe is an AutoPkg ["shared recipe processor"](https://github.com/autopkg/autopkg/wiki/Processor-Locations#shared-recipe-processors). It's a "stub" recipe that makes the MacPatchImporter processor available to your other recipes. The other ".macpatch" recipes in this repo use that stub to access the "MacPatchImporterProcessor.py" processor.

#### Setup

###### Add repo

```shell
autopkg repo-add https://github.com/SMSG-MAC-DEV/MacPatch-AutoPKG.git
```

###### Configure MacPatch environment settings
Some settings can be set for all .macpatch recipes in the AutoPkg preferences.

```shell
defaults write com.github.autopkg MP_URL https://macpatch.company.com
defaults write com.github.autopkg MP_USER autopkg
defaults write com.github.autopkg MP_PASSWORD password
defaults write com.github.autopkg MP_SSL -bool NO
```

###### Create override for a recipe
It's best to use [overrides](https://github.com/autopkg/autopkg/wiki/Recipe-Overrides) to set the recipe specific inputs for your environment. 

```shell
autopkg make-override Firefox.macpatch
```

Only keep the keys that you alter. Remove any unchanged keys from the override file.

###### Pre-install, post-install, and criteria scripts
Scripts for criteria and pre/post-install are not included directly in the recipe xml. Instead they are placed into a sub-folder of the recipe named scripts, and the corresponding keys in the recipe are set to true.

Key | Script location | Comments
----|------|------
patch_criteria_scripts | ./scripts/*.criteria-script | Any number of files with ".criteria-script" file extension.
pkg_preinstall | ./scripts/preinstall.script 
pkg_postinstall | ./scripts/postinstall.script

#### Example recipe
Below is a sample Firefox recipe with the needed inputs to upload to a MacPatch server.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Description</key>
    <string>Downloads Firefox into MacPatch.</string>

    <key>Identifier</key>
    <string>com.github.smsg-mac-dev.macpatch.firefox</string>

    <key>Input</key>
    <dict>
        <key>auth_user</key>
        <string>autopkg</string>

        <key>auth_pass</key>
        <string>password</string>

        <key>mp_server_url</key>
        <string>https://macpatch.company.com</string>

        <key>verify_ssl</key>
        <true/>

        <key>patch_name</key>
        <string>Firefox</string>

        <key>description</key>
        <string>Firefox browser.</string>

        <key>description_url</key>
        <string>http://www.mozilla.org/en-US/firefox/</string>

        <key>patch_vendor</key>
        <string>Mozilla</string>

        <key>patch_severity</key>
        <string>High</string>

        <key>OSType</key>
        <string>Mac OS X, Mac OS X Server</string>

        <key>OSVersion</key>
        <string>*</string>

        <key>patch_criteria</key>
        <array>
            <string>File@Exists@/Applications/Firefox.app@True</string>
            <string>File@VERSION@/Applications/Firefox.app@#version#;LT</string>
        </array>

        <key>patch_criteria_scripts</key>
        <false/>

        <key>pkg_preinstall</key>
        <true/>

        <key>pkg_postinstall</key>
        <false/>

        <key>pkg_env_var</key>
        <string></string>

        <key>patch_install_weight</key>
        <string>30</string>

        <key>patch_reboot</key>
        <string>No</string>
    </dict>

    <key>MinimumVersion</key>
    <string>0.2.0</string>

    <key>ParentRecipe</key>
    <string>com.github.autopkg.pkg.Firefox_EN</string>

    <key>Process</key>
    <array>
        <dict>
            <key>Arguments</key>
            <dict>
            </dict>
            <key>Processor</key>
            <string>com.github.smsg-mac-dev.MacPatchImporterProcessor/MacPatchImporterProcessor</string>
        </dict>
    </array>
</dict>
</plist>
```