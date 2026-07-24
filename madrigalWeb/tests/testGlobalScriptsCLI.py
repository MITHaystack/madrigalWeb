"""testGlobalScriptsCLI is a command-line (subprocess) unittest for the three
stand-alone global* CLI scripts: globalDownload.py, globalIsprint.py, and
globalCitation.py.

The scripts run all of their logic at module level (argument parsing, server
construction, and the download/print loop), so they are exercised here by
invoking them as subprocesses rather than by import.

Tests are split into two groups:

  * offline tests - argument validation (required args, choices, date formats,
                    directory guards) that fails BEFORE any network call.  These
                    are fast, deterministic, and need no connectivity.

  * online tests  - full happy-path runs against cedar.openmadrigal.org.  These
                    are skipped unless the environment variable MADRIGAL_ONLINE=1
                    is set, so the default test run stays offline and fast.

To run offline validation only (the default):

    python -m unittest madrigalWeb.tests.testGlobalScriptsCLI

To include the network happy-path tests against cedar:

    MADRIGAL_ONLINE=1 python -m unittest madrigalWeb.tests.testGlobalScriptsCLI

NOTE on dates: globalDownload.py and globalIsprint.py parse dates as MM/DD/YYYY
(despite their --help text saying YYYY-MM-DD), while globalCitation.py requires
YYYY-MM-DD.  These tests pin each script's actual accepted format.

Written as a command-line companion to testMadrigalWeb.py.
"""

# standard python modules
import unittest
import os
import os.path
import sys
import subprocess
import tempfile

# module to test
import madrigalWeb.madrigalWeb

# directory holding the global* scripts (one level up from this tests/ dir)
SCRIPT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# only run network tests when explicitly requested
ONLINE = 1

# constants shared with testMadrigalWeb.py conventions
URL = 'https://cedar.openmadrigal.org'
USER = ['--user_fullname=CI_Test',
        '--user_email=citest@example.com',
        '--user_affiliation=Test']


def run(script, args, stdin=None, timeout=600):
    """run invokes one of the global* scripts as a subprocess.

    Inputs:

        script - the script filename (e.g. 'globalDownload.py'), found in SCRIPT_DIR

        args - a list of command line argument strings

        stdin - optional string fed to the process's standard input (used to
                answer the globalCitation.py y/n prompt)

        timeout - max seconds to allow the subprocess to run

    Returns:

        a tuple (returncode, stdout, stderr)
    """
    # DEBUG
    #print(f"command is {" ".join([script]+args)}")

    cwd = os.getcwd()
    os.chdir("/tmp")
    proc = subprocess.run(
        [script] + args,
        input=stdin, capture_output=True, text=True, timeout=timeout)
    os.chdir(cwd)
    return (proc.returncode, proc.stdout, proc.stderr)


class TestGlobalDownloadCLI(unittest.TestCase):
    """Command-line tests of globalDownload.py"""

    # ---- offline: help / usage ----

    def test_help_flag_exits_zero(self):
        rc, out, err = run('globalDownload.py', ['--help'])
        self.assertEqual(rc, 0)
        self.assertTrue((out + err).find('globalDownload.py') != -1)

    def test_no_args_errors(self):
        rc, out, err = run('globalDownload.py', [])
        self.assertNotEqual(rc, 0)
        self.assertTrue((out + err).lower().find('required') != -1)

    # ---- offline: required args are enforced ----

    def test_missing_url(self):
        rc, out, err = run('globalDownload.py',
            ['--outputDir=/tmp'] + USER + ['--format=hdf5',
             '--startDate=01/19/1998', '--endDate=01/21/1998'])
        self.assertNotEqual(rc, 0)
        self.assertTrue((out + err).find('--url') != -1)

    def test_missing_startdate_enddate_required(self):
        # --startDate/--endDate are required=True in this script
        rc, out, err = run('globalDownload.py',
            ['--url=' + URL, '--outputDir=/tmp'] + USER + ['--format=hdf5'])
        self.assertNotEqual(rc, 0)

    # ---- offline: format choices are constrained ----

    def test_invalid_format_rejected(self):
        rc, out, err = run('globalDownload.py',
            ['--url=' + URL, '--outputDir=/tmp'] + USER + ['--format=csv',
             '--startDate=01/19/1998', '--endDate=01/21/1998'])
        self.assertNotEqual(rc, 0)
        self.assertTrue((out + err).find('csv') != -1)
        for good in ('ascii', 'hdf5', 'netCDF4'):
            self.assertTrue((out + err).find(good) != -1)

    # ---- offline: date parsing (MM/DD/YYYY, despite help text) ----

    def test_startdate_wrong_separator_errors(self):
        # ISO form is REJECTED here even though --help says YYYY-MM-DD
        rc, out, err = run('globalDownload.py',
            ['--url=' + URL, '--outputDir=/tmp'] + USER + ['--format=hdf5',
             '--startDate=1998-01-19', '--endDate=01/21/1998'])
        self.assertTrue((out + err).find('--startDate must be in the form MM/DD/YYYY') != -1)

    def test_startdate_month_out_of_range(self):
        rc, out, err = run('globalDownload.py',
            ['--url=' + URL, '--outputDir=/tmp'] + USER + ['--format=hdf5',
             '--startDate=13/01/1998', '--endDate=01/21/1998'])
        self.assertTrue((out + err).find('MM/DD/YYYY') != -1)

    def test_enddate_invalid_calendar_day(self):
        # 02/30 passes the <=31 check but fails datetime() -> "Invalid endDate"
        rc, out, err = run('globalDownload.py',
            ['--url=' + URL, '--outputDir=/tmp'] + USER + ['--format=hdf5',
             '--startDate=01/19/1998', '--endDate=02/30/1998'])
        self.assertTrue((out + err).find('Invalid endDate') != -1)

    # ---- online: happy paths ----

    @unittest.skipUnless(ONLINE, 'set MADRIGAL_ONLINE=1 to run network tests')
    def test_download_single_instrument(self):
        with tempfile.TemporaryDirectory() as d:
            rc, out, err = run('globalDownload.py',
                ['--url=' + URL, '--outputDir=' + d] + USER + ['--format=hdf5',
                 '--startDate=01/19/1998', '--endDate=01/21/1998',
                 '--inst=30', '--verbose'])
            self.assertEqual(rc, 0, err)
            files = os.listdir(d)
            self.assertTrue(len(files) > 0, 'expected at least one downloaded file')
            self.assertTrue(any(f.endswith('.hdf5') for f in files))

    @unittest.skipUnless(ONLINE, 'set MADRIGAL_ONLINE=1 to run network tests')
    def test_download_ascii_gets_txt_extension(self):
        # ascii -> 'simple' internally; basename should gain .txt
        with tempfile.TemporaryDirectory() as d:
            rc, out, err = run('globalDownload.py',
                ['--url=' + URL, '--outputDir=' + d] + USER + ['--format=ascii',
                 '--startDate=01/19/1998', '--endDate=01/21/1998', '--inst=30'])
            self.assertEqual(rc, 0, err)
            self.assertTrue(any(f.endswith('.txt') for f in os.listdir(d)))

    @unittest.skipUnless(ONLINE, 'set MADRIGAL_ONLINE=1 to run network tests')
    def test_tree_flag_creates_hierarchy(self):
        with tempfile.TemporaryDirectory() as d:
            rc, out, err = run('globalDownload.py',
                ['--url=' + URL, '--outputDir=' + d] + USER + ['--format=hdf5',
                 '--startDate=01/19/1998', '--endDate=01/21/1998',
                 '--inst=30', '--tree'])
            self.assertEqual(rc, 0, err)
            # --tree recreates YYYY/inst/expdir under outputDir
            self.assertTrue(os.path.isdir(os.path.join(d, '1998')))

    @unittest.skipUnless(ONLINE, 'set MADRIGAL_ONLINE=1 to run network tests')
    def test_no_files_selected_message(self):
        # impossible kindat -> "No files selected" and clean exit
        with tempfile.TemporaryDirectory() as d:
            rc, out, err = run('globalDownload.py',
                ['--url=' + URL, '--outputDir=' + d] + USER + ['--format=hdf5',
                 '--startDate=01/19/1998', '--endDate=01/21/1998',
                 '--inst=30', '--kindat=99999999'])
            self.assertTrue(out.find('No files selected') != -1)


class TestGlobalIsprintCLI(unittest.TestCase):
    """Command-line tests of globalIsprint.py"""

    def test_help_flag(self):
        rc, out, err = run('globalIsprint.py', ['--help'])
        self.assertEqual(rc, 0)

    def test_missing_parms_required(self):
        with tempfile.NamedTemporaryFile() as f:
            rc, out, err = run('globalIsprint.py',
                ['--url=' + URL, '--output=' + f.name] + USER +
                ['--startDate=01/19/1998', '--endDate=01/21/1998'])
        self.assertNotEqual(rc, 0)
        self.assertTrue((out + err).find('--parms') != -1)

    def test_invalid_format_choice(self):
        with tempfile.TemporaryDirectory() as d:
            rc, out, err = run('globalIsprint.py',
                ['--url=' + URL, '--parms=gdalt,ti', '--output=' + d] + USER +
                ['--startDate=01/19/1998', '--endDate=01/21/1998', '--format=csv'])
        self.assertNotEqual(rc, 0)
        self.assertTrue((out + err).find('csv') != -1)

    def test_format_case_sensitive(self):
        # 'hdf5' (lowercase) is NOT a valid choice here - only 'Hdf5'. Documents the
        # inconsistency vs globalDownload.py which uses lowercase 'hdf5'.
        with tempfile.TemporaryDirectory() as d:
            rc, out, err = run('globalIsprint.py',
                ['--url=' + URL, '--parms=gdalt,ti', '--output=' + d] + USER +
                ['--startDate=01/19/1998', '--endDate=01/21/1998', '--format=hdf5'])
        self.assertNotEqual(rc, 0)

    def test_startdate_bad_format(self):
        with tempfile.NamedTemporaryFile() as f:
            rc, out, err = run('globalIsprint.py',
                ['--url=' + URL, '--parms=gdalt,ti', '--output=' + f.name] + USER +
                ['--startDate=1998-01-19', '--endDate=01/21/1998'])
        self.assertNotEqual(rc, 0)
        self.assertTrue((out + err).find('MM/DD/YYYY') != -1)

    def test_format_set_but_output_not_a_dir(self):
        # when --format is given, output MUST be an existing writable dir
        with tempfile.NamedTemporaryFile() as f:   # a file, not a dir
            rc, out, err = run('globalIsprint.py',
                ['--url=' + URL, '--parms=gdalt,ti', '--output=' + f.name] + USER +
                ['--startDate=01/19/1998', '--endDate=01/21/1998', '--format=Hdf5'])
        self.assertNotEqual(rc, 0)
        self.assertTrue((out + err).find('must be a writable directory') != -1)

    # ---- online: happy paths ----

    @unittest.skipUnless(ONLINE, 'set MADRIGAL_ONLINE=1 to run network tests')
    def test_isprint_single_ascii_file(self):
        with tempfile.TemporaryDirectory() as d:
            out_file = os.path.join(d, 'out.txt')
            rc, out, err = run('globalIsprint.py',
                ['--url=' + URL, '--parms=gdalt,ti', '--output=' + out_file] + USER +
                ['--startDate=01/19/1998', '--endDate=01/21/1998', '--inst=30'])
            self.assertEqual(rc, 0, err)
            self.assertTrue(os.path.exists(out_file))
            with open(out_file) as fh:
                content = fh.read()
            self.assertTrue(content.find('gdalt') != -1)  # header printed unless --hideParms

    @unittest.skipUnless(ONLINE, 'set MADRIGAL_ONLINE=1 to run network tests')
    def test_isprint_hdf5_to_directory(self):
        with tempfile.TemporaryDirectory() as d:
            rc, out, err = run('globalIsprint.py',
                ['--url=' + URL, '--parms=gdalt,ti', '--output=' + d] + USER +
                ['--startDate=01/19/1998', '--endDate=01/21/1998',
                 '--inst=30', '--format=Hdf5'])
            self.assertEqual(rc, 0, err)
            self.assertTrue(any(f.endswith('.hdf5') for f in os.listdir(d)))

    @unittest.skipUnless(ONLINE, 'set MADRIGAL_ONLINE=1 to run network tests')
    def test_isprint_with_filter(self):
        with tempfile.TemporaryDirectory() as d:
            out_file = os.path.join(d, 'out.txt')
            rc, out, err = run('globalIsprint.py',
                ['--url=' + URL, '--parms=gdalt,ti', '--output=' + out_file] + USER +
                ['--startDate=01/19/1998', '--endDate=01/21/1998',
                 '--inst=30', '--filter=gdalt,500,600'])
            self.assertEqual(rc, 0, err)
            self.assertTrue(os.path.exists(out_file))


class TestGlobalCitationCLI(unittest.TestCase):
    """Command-line tests of globalCitation.py

    NOTE: globalCitation.py has no --url (it always targets cedar.openmadrigal.org)
    and prompts on stdin for y/n before creating a PERMANENT citation.  No online
    test answers 'y' here, since that would create an irreversible production
    citation.  The decline path (stdin='n') safely exercises everything up to that
    point.
    """

    def test_help_flag(self):
        rc, out, err = run('globalCitation.py', ['--help'])
        self.assertEqual(rc, 0)

    def test_missing_user_fullname(self):
        rc, out, err = run('globalCitation.py',
            ['--user_email=a@b.c', '--user_affiliation=X',
             '--startDate=1998-01-01', '--endDate=1998-02-01', '--inst=30'])
        self.assertNotEqual(rc, 0)
        self.assertTrue((out + err).find('user_fullname') != -1)

    def test_startdate_must_be_iso(self):
        # unlike the other two scripts, this one requires YYYY-MM-DD (strptime)
        rc, out, err = run('globalCitation.py',
            USER + ['--startDate=01/01/1998', '--endDate=1998-02-01', '--inst=30'])
        self.assertNotEqual(rc, 0)
        self.assertTrue((out + err).find('startDate must be in format YYYY-MM-DD') != -1)

    def test_enddate_must_be_iso(self):
        rc, out, err = run('globalCitation.py',
            USER + ['--startDate=1998-01-01', '--endDate=02/01/1998', '--inst=30'])
        self.assertNotEqual(rc, 0)
        self.assertTrue((out + err).find('endDate must be in format YYYY-MM-DD') != -1)

    def test_missing_startdate_errors(self):
        # startDate defaults to None; strptime(None) raises -> parser.error.  Documents
        # that startDate is effectively required despite not being required=True.
        rc, out, err = run('globalCitation.py',
            USER + ['--endDate=1998-02-01', '--inst=30'])
        self.assertNotEqual(rc, 0)

    def test_datelist_bad_element_errors(self):
        rc, out, err = run('globalCitation.py',
            USER + ['--startDate=1998-01-01', '--endDate=1998-02-01',
             '--inst=30', '--dateList=1998-01-01,notadate'])
        self.assertNotEqual(rc, 0)

    # ---- online: list citations, then DECLINE at the prompt (creates nothing) ----

    @unittest.skipUnless(ONLINE, 'set MADRIGAL_ONLINE=1 to run network tests')
    def test_lists_then_declines(self):
        rc, out, err = run('globalCitation.py',
            USER + ['--startDate=1998-01-01', '--endDate=1998-02-01', '--inst=30'],
            stdin='n\n')                            # answer "no" to the y/n prompt
        # declining exits nonzero and must NOT print "Created group citation"
        self.assertNotEqual(rc, 0)
        self.assertTrue(out.find('file citations will be in this group') != -1)
        self.assertTrue(out.find('Created group citation') == -1)


testCaseList = (TestGlobalDownloadCLI,
                TestGlobalIsprintCLI,
                TestGlobalCitationCLI)

suite = unittest.TestSuite()
for testCase in testCaseList:
    tests = unittest.TestLoader().loadTestsFromTestCase(testCase)
    suite.addTests(tests)
unittest.TextTestRunner(verbosity=2).run(suite)
