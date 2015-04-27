#!/usr/bin/env python
#


import os
import subprocess
import FoundationPlist
import shutil

import requests
import json
import zipfile
import glob
import base64

from autopkglib import Processor, ProcessorError


__all__ = ["MacPatchImporterProcessor"]


class MPWebService(object):
    """Post patch to MacPatch server"""

    get_auth_method_param = {'method': 'GetAuthToken'}
    post_data_method_param = {'method': 'postAutoPKGPatch'}
    get_method = ':2600/Service/MPAdminService.cfc'
    post_method = ':2600/Service/MPAutoPKGUpload.cfm'
    timeout = 15

    def __init__(self, server_name, params, verify=True):
        super(MPWebService, self).__init__()

        self._server_name = server_name.rstrip('/')
        self._verify = verify
        self._user = params['authUser']
        self._token = None
        self._patch_id = None

        self.auth(params)

    def auth(self, params):
        url = self._server_name + self.get_method
        params.update(self.get_auth_method_param)

        resp = requests.get(url, params=params, verify=self._verify, timeout=self.timeout)

        resp.raise_for_status()
        errorno = int(resp.json()['errorno'])
        errormsg = resp.json()['errormsg']
        self._token = resp.json()['result']

        if errorno != 0:
        #     print 'The MacPatch web service returned error: "{0} {1}"'.format(errorno, errormsg)
        #     print 'Responce:', resp.json()
        #     return False
            e = 'Error: "{0} {1}\nResponce: {2}"'.format(errorno, errormsg, resp.json())
            raise Exception(e)

        return True

    def post_data(self, patch_data):
        url = self._server_name + self.get_method
        params = {'user': self._user, 'token': self._token, 'autoPKGData': json.dumps(patch_data)}
        params.update(self.post_data_method_param)

        resp = requests.get(url, params=params, verify=self._verify, timeout=self.timeout)

        resp.raise_for_status()
        errorno = int(resp.json()['errorno'])
        errormsg = resp.json()['errormsg']
        self._patch_id = resp.json()['result']

        if errorno != 0:
            # print 'The MacPatch web service returned error: "{0} {1}"'.format(errorno, errormsg)
            # print 'Responce:', resp.json()
            # return False
            e = 'Error: "{0} {1}\nResponce: {2}"'.format(errorno, errormsg, resp.json())
            raise Exception(e)

        return True

    def post_pkg(self, pkg_path):
        url = self._server_name + self.post_method

        zip_path = os.path.join(pkg_path + '.zip')
        pkg_filename = os.path.basename(pkg_path)

        with zipfile.ZipFile(zip_path, mode='w') as zip_file:
            zip_file.write(pkg_path, pkg_filename, zipfile.ZIP_DEFLATED)

        data = {'userID': self._user, 'token': self._token, 'patchID': self._patch_id}
        pkg_file = {'autoPKG': open(zip_path, 'rb')}
        resp = requests.post(url, data=data, files=pkg_file, verify=self._verify, timeout=self.timeout)

        resp.raise_for_status()
        errorno = int(resp.json()['errorno'])
        errormsg = resp.json()['errormsg']
        result = resp.json()['result']

        if errorno != 0:
            # print 'The MacPatch web service returned error: "{0} {1}"'.format(errorno, errormsg)
            # print 'Responce:', resp.json()
            e = 'Error: "{0} {1}\nResponce: {2}"'.format(errorno, errormsg, resp.json())
            raise Exception(e)

        return True

    def patch_id(self):
        return self._patch_id

    def token(self):
        return self._token


class MacPatchImporterProcessor(Processor):
    """Imports a pkg into MacPatch."""
    input_variables = {
        "MP_USER": {
            "required": True,
            "description": "MacPatch autopkg web service user name, can be set system wide in the com.github.autopkg plist.",
        },
        "MP_PASSWORD": {
            "required": True,
            "description": "MacPatch utopkg web service password, can be set system wide in the com.github.autopkg plist.",
        },
        "MP_URL": {
            "required": True,
            "description": "MacPatch server url, can be set system wide in the com.github.autopkg plist.",
        },
        "MP_SSL": {
            "required": True,
            "description": "Set to False to ignore ssl errors, can be set system wide in the com.github.autopkg plist.",
        },
        "patch_name": {
            "required": True,
            "description": "Patch name.",
        },
        "description": {
            "required": True,
            "description": "Patch description.",
        },
        "patch_vendor": {
            "required": True,
            "description": "Patch vendor name.",
        },
        "description_url": {
            "required": True,
            "description": "URL to more info about the patch/software.",        
        },
        "patch_severity": {
            "required": True,
            "description": "Severity level for patch. 'High', 'Medium', 'Low', 'Unkown'.",
        },
        "OSType": {
            "required": True,
            "description": "Required OS type for patch. 'Mac OS X, Mac OS X Server', 'Mac OS X' or 'Mac OS X Server'",
        },
        "OSVersion": {
            "required": True,
            "description": "Required OS versions for patch. '10.9.*', '10.8.*, 10.9.*' etc. Use '*' for all OS versions.",
        },
        "patch_criteria": {
            "required": True,
            "description": "A list of patch criteria, in order of evaluation. Type and data, ie 'File' 'File@/path/file@exists@True'",
        },
        "bundleid": {
            "required": False,
            "description": "Bundle-id for patch. ex: 'org.mozilla.firefox'. Default is to use bundleid from parent recipe.",
        },
        "pkg_preinstall": {
            "required": True,
            "description": "True/False if preinstall script is to be uploaded. If True, create a folder named 'scripts' and a script named 'preinstall.script'.",
        },
        "pkg_postinstall": {
            "required": True,
            "description": "True/False if postinstall script is to be uploaded. If True, create a folder named 'scripts' and a script named 'postinstall.script'.",
        },
        "pkg_env_var": {
            "required": True,
            "description": "Env variables for installer. 'myvar=test,foo=tmp'",
        },
        "patch_install_weight": {
            "required": True,
            "description": "Patch install weight. For default value set this to 30.",
        },
        "patch_reboot": {
            "required": True,
            "description": "Does the patch require a reboot. 'Yes', 'No'",
        },
    }

    output_variables = {
        "puuid": {
            "description": "The puuid of the patch."
        },
        "patch_uploaded": {
            "description": "True if patch was uploaded successfully."
        },
    }
    description = __doc__


    def main(self):
        # if not self.env['download_changed']:
        #     print 'No new updates where downloaded, nothing to upload.'.format(self.env['patch_name'])
        #     exit(0)

        mp_server = self.env['MP_URL']
        user_params = {
            'authUser': self.env['MP_USER'],
            'authPass': self.env['MP_PASSWORD'],
            }

        payload = {
            'patch_name': self.env['patch_name'],
            'description': self.env['description'],
            'description_url': self.env['description_url'],
            'patch_vendor': self.env['patch_vendor'],
            'patch_severity': self.env['patch_severity'],
            'OSType': self.env['OSType'],
            'OSVersion': self.env['OSVersion'],
            'pkg_env_var': self.env['pkg_env_var'],
            'patch_install_weight': self.env['patch_install_weight'],
            'patch_reboot': self.env['patch_reboot'],
            'bundle_id': self.env['bundleid'],
            'patch_ver': self.env['version'],
            }

        if self.env['pkg_preinstall']:
            pkg_preinstall_path = os.path.join(self.env['RECIPE_DIR'], 'scripts/preinstall.script')
            if os.path.isfile(pkg_preinstall_path):
                with open(pkg_preinstall_path, 'r') as f:
                    payload['pkg_preinstall'] = base64.encodestring(f.read())

        if self.env['pkg_postinstall']:
            pkg_postinstall_path = os.path.join(self.env['RECIPE_DIR'], 'scripts/postinstall.script')
            if os.path.isfile(pkg_postinstall_path):
                with open(pkg_postinstall_path, 'r') as f:
                    payload['pkg_postinstall'] = base64.encodestring(f.read())

        if self.env['patch_criteria']:
            payload['patch_criteria_enc'] = [base64.encodestring(x.replace('#version#', self.env['version'])) for x in self.env['patch_criteria']]
        else:
            payload['patch_criteria_enc'] = []

        if self.env['patch_criteria_scripts']:
            c_scripts_path = os.path.join(self.env['RECIPE_DIR'], 'scripts')
            c_scripts = glob.glob(c_scripts_path + '/*.criteria-script')
            if c_scripts:
                for script in c_scripts:
                    with open(script, 'r') as f:
                        c = base64.encodestring('Script@' + f.read().replace('#version#', self.env['version']))
                        payload['patch_criteria_enc'].append(c)

        try:
            mp_webservice = MPWebService(mp_server, user_params, verify=self.env['MP_SSL'])
            mp_webservice.post_data(payload)
            self.env['patch_uploaded'] = mp_webservice.post_pkg(self.env['pkg_path'])
        except Exception, e:
            print 'Something went wrong while communicating with the web service.'
            print e
            exit(1)
        
        self.env['puuid'] = mp_webservice.patch_id()

        print '\n'
        print 'Patch Name:      ', self.env['patch_name']
        print 'Patch ID:        ', self.env['puuid']
        print 'Patch Uploaded:  ', self.env['patch_uploaded']

if __name__ == "__main__":
    processor = MacPatchImporterProcessor()
    processor.execute_shell()