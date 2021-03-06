""" :module casim_test: Test module for casim."""

# Import class to be tested.
from casim import casim
from casim.casim import CancerSimulator, CancerSimulatorParameters, check_set_number, load_cancer_simulation

from collections import namedtuple
from test_utilities import _remove_test_files
from io import StringIO
import numpy
import logging
from subprocess import Popen
import re
import os
import sys
import unittest
import pickle
import pandas
from tempfile import mkdtemp

logging.getLogger().setLevel(logging.DEBUG)

class CancerSimulatorParametersTest(unittest.TestCase):
    """ :class: Test class for the CancerSimulator """

    @classmethod
    def setUpClass(cls):
        """ Setup the test class. """

        # Setup a list of test files.
        cls._static_test_files = []

    @classmethod
    def tearDownClass(cls):
        """ Tear down the test class. """

        _remove_test_files(cls._static_test_files)

    def setUp (self):
        """ Setup the test instance. """

        # Setup list of test files to be removed immediately after each test method.
        self._test_files = []

    def tearDown (self):
        """ Tear down the test instance. """
        _remove_test_files(self._test_files)

    def test_default_constructor (self):
        """ Test initialization without arguments. """

        parameters = CancerSimulatorParameters()

        self.assertEqual(parameters.matrix_size, 10)
        self.assertEqual(parameters.number_of_generations, 2)
        self.assertEqual(parameters.division_probability, 1)
        self.assertEqual(parameters.adv_mutant_division_probability, 1)
        self.assertEqual(parameters.death_probability, 0)
        self.assertEqual(parameters.adv_mutant_death_probability, 0.0)
        self.assertEqual(parameters.mutation_probability, 0.8)
        self.assertEqual(parameters.adv_mutant_mutation_probability, 1)
        self.assertEqual(parameters.number_of_mutations_per_division, 1)
        self.assertEqual(parameters.adv_mutation_wait_time, 50000)
        self.assertEqual(parameters.number_of_initial_mutations, 1)
        self.assertEqual(parameters.tumour_multiplicity, 'single')
        self.assertEqual(parameters.read_depth, 100)
        self.assertEqual(parameters.sampling_fraction, 0.0)
        self.assertIsNone(parameters.sampling_positions)
        self.assertTrue(parameters.plot_tumour_growth)
        self.assertTrue(parameters.export_tumour)

    def test_shaped_constructor (self):
        """ Test initialization with arguments. """

        parameters=CancerSimulatorParameters(
                                matrix_size=20  ,
                                number_of_generations=10  ,
                                division_probability=0.5,
                                adv_mutant_division_probability=0.3,
                                death_probability=0.1,
                                adv_mutant_death_probability=0.4,
                                mutation_probability=0.2,
                                adv_mutant_mutation_probability=0.8,
                                number_of_mutations_per_division=10  ,
                                adv_mutation_wait_time=30000  ,
                                number_of_initial_mutations=2  ,
                                tumour_multiplicity='single',
                                read_depth=200,
                                sampling_fraction=0.3,
                                sampling_positions=[(13,12), (3,6)],
                                export_tumour=False,
                                plot_tumour_growth=False,
                                                )

        self.assertEqual(parameters.matrix_size, 20)
        self.assertEqual(parameters.number_of_generations, 10)
        self.assertEqual(parameters.division_probability, 0.5)
        self.assertEqual(parameters.adv_mutant_division_probability, 0.3)
        self.assertEqual(parameters.death_probability, 0.1)
        self.assertEqual(parameters.adv_mutant_death_probability, 0.4)
        self.assertEqual(parameters.mutation_probability, 0.2)
        self.assertEqual(parameters.adv_mutant_mutation_probability, 0.8)
        self.assertEqual(parameters.number_of_mutations_per_division, 10)
        self.assertEqual(parameters.adv_mutation_wait_time, 30000)
        self.assertEqual(parameters.number_of_initial_mutations, 2)
        self.assertEqual(parameters.tumour_multiplicity, 'single' )
        self.assertEqual(parameters.read_depth, 200 )
        self.assertEqual(parameters.sampling_fraction, 0.3 )
        self.assertEqual(numpy.linalg.norm(parameters.sampling_positions - numpy.array([[13,12], [3,6]])), 0)
        self.assertFalse(parameters.plot_tumour_growth)
        self.assertFalse(parameters.export_tumour)

    def test_check_set_number(self):
        """ Test the numer checking utility. """

        self.assertEqual(1, check_set_number(1, int))
        self.assertEqual(1, check_set_number(1, int, None, 0, 10))
        self.assertEqual(1, check_set_number(1.0, int, None, 0, 10))

        self.assertRaises(TypeError, check_set_number, numpy.array([1.,2.]), float)


class CancerSimulatorTest(unittest.TestCase):
    """ :class: Test class for the CancerSimulator """

    @classmethod
    def setUpClass(cls):
        """ Setup the test class. """

        # Setup a list of test files.
        cls._static_test_files = []

    @classmethod
    def tearDownClass(cls):
        """ Tear down the test class. """

        _remove_test_files(cls._static_test_files)

    def setUp (self):
        """ Setup the test instance. """

        # Setup list of test files to be removed immediately after each test method.
        self._test_files = []

    def tearDown (self):
        """ Tear down the test instance. """
        _remove_test_files(self._test_files)

    def test_default_constructor (self):
        """ Test the construction of the Simulator without arguments. """

        # Cleanup.
        self._test_files.append("casim_out")

        # Test that the Simulator cannot be constructed without parameters.
        with self.assertRaises(ValueError):
            casim = CancerSimulator()

    def test_setup_io(self):
        """ Test the IO handling. """

        default_parameters = CancerSimulatorParameters()

        # Setup the simulator without outdir.
        cancer_sim = CancerSimulator(default_parameters, seed=1)
        self._test_files.append("casim_out")

        # Test it is set to the default path in CWD.
        self.assertEqual(cancer_sim.outdir, "casim_out")

        # Get seed dir.
        seeddir = os.path.join("casim_out", 'cancer_%d' % cancer_sim._CancerSimulator__seed)
        # Check all subdirectories are correctly named and exist.
        self.assertEqual(cancer_sim._CancerSimulator__logdir, os.path.join(seeddir, 'log'))
        self.assertTrue(os.path.isdir(cancer_sim._CancerSimulator__logdir))
        self.assertEqual(cancer_sim._CancerSimulator__simdir, os.path.join(seeddir, 'simOutput'))
        self.assertTrue(os.path.isdir(cancer_sim._CancerSimulator__simdir))

        # Create an empty dir.
        tmpdir = mkdtemp()
        self._test_files.append(tmpdir)

        # Set to a different dir.
        cancer_sim.outdir = tmpdir

        # Check export_tumour flag.
        self.assertTrue(cancer_sim.parameters.export_tumour)

        # Check exception is thrown if same O dir is used twice.
        with self.assertRaises(IOError) as exc:
            cancer_sim.outdir = tmpdir
    
    def test_params_module(self):
        """ Check that starting a run with params.py paramters sets all
        parameters correctly. """

        arguments = namedtuple('arguments', ('params', 'seed', 'outdir', 'loglevel'))
        arguments.seed = 1
        arguments.params = '../casim/params.py'
        arguments.outdir='cancer_sim_out'
        arguments.loglevel = 1
        self._test_files.append(arguments.outdir)

        # Capture stdout.
        stream = StringIO()
        log = logging.getLogger()
        for handler in log.handlers:
           log.removeHandler(handler)
        myhandler = logging.StreamHandler(stream)
        myhandler.setLevel(logging.DEBUG)
        log.addHandler(myhandler)

        # Run the simulation.
        casim.main(arguments)

        # Flush log.
        myhandler.flush()

        # Read stdout.
        sim_out = stream.getvalue()

        # Reset stdout.
        log.removeHandler(myhandler)
        handler.close()

        # target = re.compile(r"^.*sampling_fraction\s=\s0\.1.*$")
        target = re.compile(r'matrix_size\s=\s1000')
        self.assertRegex(sim_out, target)

        target = re.compile(r'number_of_generations\s=\s20')
        self.assertRegex(sim_out, target)

        target = re.compile(r'division_probability\s=\s1\.0')
        self.assertRegex(sim_out, target)

        target = re.compile(r'adv_mutant_division_probability\s=\s1\.0')
        self.assertRegex(sim_out, target)

        target = re.compile(r'death_probability\s=\s0\.1')
        self.assertRegex(sim_out, target)

        target = re.compile(r'adv_mutant_death_probability\s=\s0\.0')
        self.assertRegex(sim_out, target)

        target = re.compile(r'mutation_probability\s=\s1\.0')
        self.assertRegex(sim_out, target)

        target = re.compile(r'adv_mutant_mutation_probability\s=\s1\.0')
        self.assertRegex(sim_out, target)

        target = re.compile(r'number_of_mutations_per_division\s=\s10')
        self.assertRegex(sim_out, target)

        target = re.compile(r'adv_mutation_wait_time\s=\s10')
        self.assertRegex(sim_out, target)

        target = re.compile(r'number_of_initial_mutations\s=\s150')
        self.assertRegex(sim_out, target)

        target = re.compile(r'tumour_multiplicity\s=\ssingle')
        self.assertRegex(sim_out, target)

        target = re.compile(r'read_depth\s=\s100')
        self.assertRegex(sim_out, target)

        target = re.compile(r'sampling_fraction\s=\s0\.1')
        self.assertRegex(sim_out, target)

        target = re.compile(r'plot_tumour_growth\s=\sTrue')
        self.assertRegex(sim_out, target)

        target = re.compile(r'export_tumour\s=\sTrue')
        self.assertRegex(sim_out, target)
        
    def test_high_sampling_fraction(self):
        """ Test run with sampling_fraction=0.9 """

        # Setup parameters.
        parameters = CancerSimulatorParameters(
                                            matrix_size=1000,
                                            number_of_generations=20,
                                            division_probability=1,
                                            adv_mutant_division_probability=1,
                                            death_probability=0.1,
                                            adv_mutant_death_probability=0.0,
                                            mutation_probability=1,
                                            adv_mutant_mutation_probability=1,
                                            adv_mutation_wait_time=10,
                                            number_of_initial_mutations=150,
                                            number_of_mutations_per_division=50,
                                            tumour_multiplicity=None,
                                            read_depth=100,
                                            sampling_fraction=0.9,
                                            )

        # Setup the simulator.
        simulator = CancerSimulator(parameters=parameters, seed=1, outdir=mkdtemp())
        # Cleanup (remove test output).
        self._test_files.append(simulator.outdir)

        # Check run returns sanely.
        self.assertEqual(simulator.run(), 0)

    def test_reference_data_50mut(self):
        """ Run a reference test and compare against reference data."""
        """ 50 mutations per division."""

        # Setup parameters. Values taken from casim/params.py.
        parameters = CancerSimulatorParameters(
                                            matrix_size=1000,
                                            number_of_generations=20,
                                            division_probability=1,
                                            adv_mutant_division_probability=1,
                                            death_probability=0.1,
                                            adv_mutant_death_probability=0.0,
                                            mutation_probability=1,
                                            adv_mutant_mutation_probability=1,
                                            adv_mutation_wait_time=10,
                                            number_of_initial_mutations=150,
                                            number_of_mutations_per_division=50,
                                            tumour_multiplicity=None,
                                            sampling_fraction=0.1,
                                            )

        simulator = CancerSimulator(parameters=parameters, seed=1, outdir="reference_test_out")
        self._test_files.append('reference_test_out')

        simulator.run()

        ### Load results and reference data.
        # Reference data.
        ref_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'reference_test_data_50mut', 'cancer_1', 'simOutput')
        with open(os.path.join(ref_dir, 'mtx.p'), 'rb') as fp:
            ref_mtx = pickle.load(fp)
        with open(os.path.join(ref_dir, 'mut_container.p'), 'rb') as fp:
            ref_mutations = pickle.load(fp)


        run_dir = os.path.join('reference_test_out', 'cancer_1', 'simOutput')
        # Run data.
        with open(os.path.join(run_dir, 'mtx.p'), 'rb') as fp:
            run_mtx = pickle.load(fp)
        with open(os.path.join(run_dir, 'mut_container.p'), 'rb') as fp:
            run_mutations = pickle.load(fp)

        # Check data is equal.
        self.assertAlmostEqual(numpy.linalg.norm((ref_mtx - run_mtx).toarray()), 0.0)
        self.assertEqual(ref_mutations, run_mutations)

    def test_reference_data_1mut(self):
        """ Run a reference test and compare against reference data."""
        """ 1 mutation per division."""

        # Setup parameters. Values taken from casim/params.py.
        parameters = CancerSimulatorParameters(
                                            matrix_size=1000,
                                            number_of_generations=20,
                                            division_probability=1,
                                            adv_mutant_division_probability=1,
                                            death_probability=0.1,
                                            adv_mutant_death_probability=0.0,
                                            mutation_probability=1,
                                            adv_mutant_mutation_probability=1,
                                            adv_mutation_wait_time=10,
                                            number_of_initial_mutations=150,
                                            number_of_mutations_per_division=1,
                                            tumour_multiplicity=None,
                                            sampling_fraction=0.1,
                                            sampling_positions=[(501,502)],
                                            )

        simulator = CancerSimulator(parameters=parameters, seed=1, outdir="reference_test_out")
        self._test_files.append('reference_test_out')

        simulator.run()

        ### Load results and reference data.
        # Reference data.
        ref_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'reference_test_data_1mut', 'cancer_1', 'simOutput')
        with open(os.path.join(ref_dir, 'mtx.p'), 'rb') as fp:
            ref_mtx = pickle.load(fp)
        with open(os.path.join(ref_dir, 'mut_container.p'), 'rb') as fp:
            ref_mutations = pickle.load(fp)

        run_dir = os.path.join('reference_test_out', 'cancer_1', 'simOutput')
        # Run data.
        with open(os.path.join(run_dir, 'mtx.p'), 'rb') as fp:
            run_mtx = pickle.load(fp)
        with open(os.path.join(run_dir, 'mut_container.p'), 'rb') as fp:
            run_mutations = pickle.load(fp)

        # Check data is equal.
        self.assertAlmostEqual(numpy.linalg.norm((ref_mtx - run_mtx).toarray()), 0.0)
        self.assertEqual(ref_mutations, run_mutations)

    def test_serialize(self):
        """ The the serialization of the entire object. """
        parameters = CancerSimulatorParameters()
        cancer_sim = CancerSimulator(parameters, seed=2, outdir=mkdtemp())

        # Cleanup.
        self._test_files.append(cancer_sim.outdir)

        # Dump.
        cancer_sim.dump()

        # Reload
        loaded_simulation = load_cancer_simulation(cancer_sim.dumpfile)
        self.assertIsInstance(loaded_simulation, CancerSimulator)

        # Check parameters.
        loaded_parameters = loaded_simulation.parameters

        self.assertEqual(loaded_parameters.number_of_generations, parameters.number_of_generations)
        self.assertEqual(loaded_parameters.matrix_size, parameters.matrix_size)
        self.assertEqual(loaded_parameters.number_of_generations, parameters.number_of_generations)
        self.assertEqual(loaded_parameters.division_probability, parameters.division_probability)
        self.assertEqual(loaded_parameters.adv_mutant_division_probability, parameters.adv_mutant_division_probability)
        self.assertEqual(loaded_parameters.death_probability, parameters.death_probability)
        self.assertEqual(loaded_parameters.adv_mutant_death_probability, parameters.adv_mutant_death_probability)
        self.assertEqual(loaded_parameters.mutation_probability, parameters.mutation_probability)
        self.assertEqual(loaded_parameters.adv_mutant_mutation_probability, parameters.adv_mutant_mutation_probability)
        self.assertEqual(loaded_parameters.number_of_mutations_per_division, parameters.number_of_mutations_per_division)
        self.assertEqual(loaded_parameters.adv_mutation_wait_time, parameters.adv_mutation_wait_time)
        self.assertEqual(loaded_parameters.number_of_initial_mutations, parameters.number_of_initial_mutations)
        self.assertEqual(loaded_parameters.tumour_multiplicity, parameters.tumour_multiplicity)
        self.assertEqual(loaded_parameters.read_depth, parameters.read_depth)
        self.assertEqual(loaded_parameters.sampling_fraction, parameters.sampling_fraction)

        # Check we can run.
        loaded_simulation.run()

        # dump again.
        loaded_simulation.dump()

        # Load again
        loaded_again_simulation = load_cancer_simulation(loaded_simulation.dumpfile)
        
        # Check that the internal state is the same as in the dump.
        self.assertAlmostEqual(numpy.linalg.norm(loaded_simulation._CancerSimulator__mtx.toarray()
            - loaded_again_simulation._CancerSimulator__mtx.toarray()), 0.0) 
        self.assertEqual(loaded_simulation._CancerSimulator__mut_container, loaded_again_simulation._CancerSimulator__mut_container) 
        self.assertEqual(loaded_simulation._CancerSimulator__xaxis_histogram, loaded_again_simulation._CancerSimulator__xaxis_histogram) 
        self.assertEqual(loaded_simulation._CancerSimulator__biopsy_timing, loaded_again_simulation._CancerSimulator__biopsy_timing) 
        self.assertEqual(loaded_simulation._CancerSimulator__beneficial_mutation, loaded_again_simulation._CancerSimulator__beneficial_mutation) 
        self.assertEqual(loaded_simulation._CancerSimulator__growth_plot_data, loaded_again_simulation._CancerSimulator__growth_plot_data) 
        self.assertEqual(loaded_simulation._CancerSimulator__mutation_counter, loaded_again_simulation._CancerSimulator__mutation_counter) 
        self.assertEqual(loaded_simulation._CancerSimulator__s, loaded_again_simulation._CancerSimulator__s) 
        self.assertEqual(loaded_simulation._CancerSimulator__ploidy, loaded_again_simulation._CancerSimulator__ploidy) 
        self.assertEqual(loaded_simulation._CancerSimulator__mut_multiplier, loaded_again_simulation._CancerSimulator__mut_multiplier) 
        self.assertEqual(loaded_simulation._CancerSimulator__pool, loaded_again_simulation._CancerSimulator__pool) 

        # Run once more.
        loaded_again_simulation.run()

    def test_init_step_increases(self):
        """ Check the the internal step counter is propely updated. """

        parameters = CancerSimulatorParameters()
        cancer_sim = CancerSimulator(parameters, seed=1, outdir = mkdtemp())

        self.assertEqual(cancer_sim._CancerSimulator__init_step, 0)
        cancer_sim.run()
        self.assertEqual(cancer_sim._CancerSimulator__init_step, 2)


    def test_export_tumour_matrix(self):
        """ Test exporting the tumour matrix. """

        parameters = CancerSimulatorParameters()
        cancer_sim = CancerSimulator(parameters, seed=1, outdir = mkdtemp())
        cancer_sim.run()

        # Check files where created.
        listing = os.listdir(cancer_sim._CancerSimulator__simdir)
        for f in ['mtx.p', 'mut_container.p', 'mtx_VAF.txt']:
            self.assertIn(f, listing)

    def test_sampling_output(self):
        """ Check that output generated by the sampling postprocessing goes to the correct path."""

        # Setup parameters.
        parameters = CancerSimulatorParameters(
                                            matrix_size=1000,
                                            number_of_generations=20,
                                            division_probability=1,
                                            adv_mutant_division_probability=1,
                                            death_probability=0.1,
                                            adv_mutant_death_probability=0.0,
                                            mutation_probability=1,
                                            adv_mutant_mutation_probability=1,
                                            adv_mutation_wait_time=10,
                                            number_of_initial_mutations=150,
                                            number_of_mutations_per_division=1,
                                            tumour_multiplicity=None,
                                            sampling_fraction=0.5,
                                            plot_tumour_growth=True,
                                            export_tumour=True,
                                            )

        simulator = CancerSimulator(parameters=parameters, seed=1, outdir="casim_out")
        # Cleanup (remove test output).
        self._test_files.append(simulator.outdir)

        # Run the simulation.
        simulator.run()

        # Check sampling file was written.
        self.assertRegex(",".join(os.listdir(simulator._CancerSimulator__simdir)), re.compile(r"sample_out_[0-9]{3}_[0-9]{3}.txt"))
        self.assertRegex(",".join(os.listdir(simulator._CancerSimulator__simdir)), re.compile(r"sampleHistogram_[0-9]{3}_[0-9]{3}.pdf"))
        self.assertIn('growthCurve.pdf', os.listdir(simulator._CancerSimulator__simdir))

    def test_sampling_positions(self):
        """ Check setting the sample positions generates the expected output."""

        # Setup parameters.
        parameters = CancerSimulatorParameters(
                                            matrix_size=1000,
                                            number_of_generations=20,
                                            division_probability=1,
                                            adv_mutant_division_probability=1,
                                            death_probability=0.1,
                                            adv_mutant_death_probability=0.0,
                                            mutation_probability=1,
                                            adv_mutant_mutation_probability=1,
                                            adv_mutation_wait_time=10,
                                            number_of_initial_mutations=150,
                                            number_of_mutations_per_division=1,
                                            tumour_multiplicity=None,
                                            sampling_fraction=0.1,
                                            sampling_positions=[
                                                [500,500],
                                                [450,550],
                                                [450,550],
                                                [550,450],
                                                [550,550],
                                                ],
                                            plot_tumour_growth=True,
                                            export_tumour=True,
                                            )

        simulator = CancerSimulator(parameters=parameters, seed=1, outdir="casim_out")
        # Cleanup (remove test output).
        self._test_files.append(simulator.outdir)

        # Run the simulation.
        simulator.run()

        # Check sampling file was written.
        self.assertIn("sample_out_500_500.txt", os.listdir(simulator._CancerSimulator__simdir))
        self.assertIn("sampleHistogram_500_500.pdf", os.listdir(simulator._CancerSimulator__simdir))
        self.assertRegex(",".join(os.listdir(simulator._CancerSimulator__simdir)), re.compile(r"sampleHistogram_[0-9]{3}_[0-9]{3}.pdf"))


class casim_test(unittest.TestCase):
    """ :class: Test class for the casim """

    @classmethod
    def setUpClass(cls):
        """ Setup the test class. """

        # Setup a list of test files.
        cls._static_test_files = []

    @classmethod
    def tearDownClass(cls):
        """ Tear down the test class. """

        _remove_test_files(cls._static_test_files)

    def setUp (self):
        """ Setup the test instance. """

        # Setup list of test files to be removed immediately after each test method.
        self._test_files = []

    def tearDown (self):
        """ Tear down the test instance. """
        _remove_test_files(self._test_files)

    def test_cli(self):
        """ Test the command line interface. """
        # Setup command.
        self._test_files.append("casim_out")
        self._test_files.append("cancer_sim_output")

        # Run with only default parameters.
        args = []

        proc = Popen("python -m casim.casim", shell=True)
        proc.wait()
        self.assertEqual(proc.returncode, 0)
        
        params_path = os.path.join(os.path.dirname("__FILE__"),"..","casim","params.py")
        out_path = "cancer_sim_output"
        seed = 2
        proc = Popen("python -m casim.casim -p {0:s} -s {1:d} -o {2:s}".format(params_path,
                                                                               seed,
                                                                               out_path),
                                                                               shell=True
                                                                               )
        proc.wait()
        self.assertEqual(proc.returncode, 0)

        # run with positional argument (long version).
        seed = 3
        proc = Popen("python -m casim.casim --params {0:s} --seed {1:d} --outdir {2:s}".format(params_path,
                                                                               seed,
                                                                               out_path),
                                                                               shell=True
                                                                               )
        proc.wait()
        self.assertEqual(proc.returncode, 0)
        
        # run with positional argument (long version) and verbosity.
        seed = 4
        proc = Popen("python -m casim.casim --params {0:s} --seed {1:d} --outdir {2:s}".format(params_path,
                                                                               seed,
                                                                               out_path),
                                                                               shell=True
                                                                               )
        proc.wait()
        self.assertEqual(proc.returncode, 0)

    def test_10x10_seed_1(self):
        """ Run a test case with 10x10 cells and prng seed 1. """

        arguments = namedtuple('arguments', ('params', 'seed', 'outdir', 'loglevel'))
        arguments.seed = 1
        arguments.params = '../casim/params.py'
        arguments.outdir='cancer_sim_out'
        arguments.loglevel = 2
        self._test_files.append(arguments.outdir)

        # Capture stdout.
        stream = StringIO()
        log = logging.getLogger()
        old_handlers = [h for h in log.handlers]
        for handler in log.handlers:
           log.removeHandler(handler)
        myhandler = logging.StreamHandler(stream)
        myhandler.setLevel(logging.DEBUG)
        log.addHandler(myhandler)

        # Run the simulation.
        casim.main(arguments)

        # Flush log.
        myhandler.flush()

        # Read stdout.
        sim_out = stream.getvalue()

        # Reset stdout.
        myhandler.close()
        log.removeHandler(myhandler)

        for oh in old_handlers:
            log.addHandler(oh)

        mut_container_regex = re.compile(r"1 \[\(1, 4.0\), \(2, 2.0\), \(3, 2.0\), \(4, 1.0\), \(5, 1.0\), \(6, 1.0\), \(7, 1.0\)\]")
        # self.assertRegex(sim_out, mut_container_regex)
    
if __name__ == "__main__":

    unittest.main()
