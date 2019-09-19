import pytest, json, os
from flask import url_for
import omf
from omf import omfDir
from omf.web import app


"""Integration tests for access control functionality"""


@pytest.fixture
def client():
    """
    Logging in with the test client works, but only if the tests are run from the inner omf directory. This is due to how web.py relies on relative
    paths to open important files. web.py must be refactored first before $ pytest $ can be run from anywhere
    """
    app.config['TESTING'] = True
    client = app.test_client()
    model_name = 'test_voltageDrop'
    # Log the test user in
    rv = client.post('/login', data={
        'username': 'test',
        'password': 'test'
    })
    assert rv.headers.get("Location") == "http://localhost/"
    assert rv.status_code == 302
    # Create two test models
    with client as c:
        model_name = 'test_voltageDrop'
        rv = c.get('/newModel/voltageDrop/' + model_name)
        assert rv.status_code == 302
        assert rv.headers.get("Location") == "http://localhost" + url_for('showModel', owner="test", modelName=model_name)
    with client as c:
        model_name = 'test_cvrDyn'
        rv = c.get('/newModel/cvrDynamic/' + model_name)
        assert rv.status_code == 302
        assert rv.headers.get("Location") == "http://localhost" + url_for('showModel', owner="test", modelName=model_name)
    # Create two test users
    test_users = ['first-test-user', 'second-test-user'] 
    for username in test_users:
        filepath = os.path.join(omfDir, 'data/User', username + '.json')
        with open(filepath, 'w') as f:
            f.write('{}')
    # Send client to test
    yield client
    # Cleanup
    client.post('/delete/Model/test/test_voltageDrop')
    client.post('/delete/Model/test/test_cvrDyn')
    for username in test_users:
        filepath = os.path.join(omfDir, 'data/User', username + '.json')
        if os.path.isfile(filepath):
            os.remove(filepath)


class TestShareModel(object):

    def test_ownerSharesWithUnauthorizedUsers_updatesModelMetadata(self, client):
        client.post('/shareModel', data={
            'user': 'test',
            'modelName': 'test_voltageDrop',
            'email': ['second-test-user', 'first-test-user']
        })
        filepath = "data/Model/test/test_voltageDrop/allInputData.json"
        with open(filepath) as f:
            model_metadata = json.load(f)
        assert sorted(model_metadata.get('viewers')) == sorted(['second-test-user', 'first-test-user'])

    def test_ownerSharesWithUnauthorizedUsers_updatesUserMetadata(self, client):
        client.post('/shareModel', data={
            'user': 'test',
            'modelName': 'test_voltageDrop',
            'email': ['second-test-user', 'first-test-user']
        })
        for filename in ['first-test-user.json', 'second-test-user.json']:
            filepath = "data/User/" + filename
            with open(filepath) as f:
                user_metadata = json.load(f)
                assert len(user_metadata.get('readonly_models')) == 1
                assert len(user_metadata.get('readonly_models').get('test')) == 1
                assert user_metadata.get('readonly_models').get('test')[0] == 'test_voltageDrop'

    def test_ownerRevokesFromUnauthroizedUsers_doesNotUpdateModelMetadata(self, client):
        """Why test this? An unauthorized user was never shared with in the first place"""
        pass

    def test_ownerRevokesFromUnauthroizedUsers_doesNotUpdateUserMetadata(self, client):
        """Why test this? An unauthorized user was never shared with in the first place"""
        pass

    def test_ownerResharesWithAuthorizedUsers_doesNotUpdateModelMetadata(self, client):
        for _ in range(2):
            client.post('/shareModel', data={
                'user': 'test',
                'modelName': 'test_voltageDrop',
                'email': ['second-test-user', 'first-test-user']
            })
        filepath = "data/Model/test/test_voltageDrop/allInputData.json"
        with open(filepath) as f:
            model_metadata = json.load(f)
        assert sorted(model_metadata.get('viewers')) == sorted(['second-test-user', 'first-test-user']) 

    def test_ownerResharesWithAuthorizedUsers_doestNotUpdateUserMetadata(self, client):
        for _ in range(2):
            client.post('/shareModel', data={
                'user': 'test',
                'modelName': 'test_voltageDrop',
                'email': ['second-test-user', 'first-test-user']
            })
        for filename in ['first-test-user.json', 'second-test-user.json']:
            filepath = os.path.join(os.path.abspath(omf.omfDir), "data/User", filename)
            with open(filepath) as f:
                user_metadata = json.load(f)
                assert len(user_metadata.get('readonly_models')) == 1
                assert len(user_metadata.get('readonly_models').get('test')) == 1
                assert user_metadata.get('readonly_models').get('test')[0] == 'test_voltageDrop'

    def test_ownerRevokesFromAuthorizedUsers_updatesModelMetadata(self, client):
        """Share two models, then revoke access to one. One should still be shared"""
        for model_name in ['test_voltageDrop', 'test_cvrDyn']:
            client.post('/shareModel', data={
                'user': 'test',
                'modelName': model_name,
                'email': ['second-test-user', 'first-test-user']
            })
        client.post('/shareModel', data={
            'user': 'test',
            'modelName': 'test_cvrDyn',
            'email': []
        })
        filepath = "data/Model/test/test_voltageDrop/allInputData.json"
        with open(filepath) as f:
            model_metadata = json.load(f)
        assert sorted(model_metadata.get('viewers')) == sorted(['second-test-user', 'first-test-user'])
        filepath = "data/Model/test/test_cvrDyn/allInputData.json"
        with open(filepath) as f:
            model_metadata = json.load(f)
        assert model_metadata.get('viewers') is None

    def test_ownerRevokesFromAuthorizedUsers_updatesUserMetadata(self, client):
        """Share two models, then revoke access to one. One should be left"""
        for model_name in ['test_voltageDrop', 'test_cvrDyn']:
            client.post('/shareModel', data={
                'user': 'test',
                'modelName': model_name,
                'email': ['second-test-user', 'first-test-user']
            })
        client.post('/shareModel', data={
            'user': 'test',
            'modelName': 'test_cvrDyn',
            'email': []
        })
        for filename in ['first-test-user.json', 'second-test-user.json']:
            filepath = "data/User/" + filename
            with open(filepath) as f:
                user_metadata = json.load(f)
                assert len(user_metadata.get('readonly_models')) == 1
                assert len(user_metadata.get('readonly_models').get('test')) == 1
                assert user_metadata.get('readonly_models').get('test')[0] == 'test_voltageDrop'

    def test_ownerSharesThenDeletesModel_removesModelFromUserMetadata(self, client):
        """Share two models, then delete one. One should be left"""
        for model_name in ['test_voltageDrop', 'test_cvrDyn']:
            client.post('/shareModel', data={
                'user': 'test',
                'modelName': model_name,
                'email': ['second-test-user', 'first-test-user']
            })
        client.post('/delete/Model/test/test_voltageDrop')
        for filename in ['first-test-user.json', 'second-test-user.json']:
            filepath = "data/User/" + filename
            with open(filepath) as f:
                user_metadata = json.load(f)
                assert len(user_metadata.get('readonly_models')) == 1
                assert len(user_metadata.get('readonly_models').get('test')) == 1
                assert user_metadata.get('readonly_models').get('test')[0] == 'test_cvrDyn'

    def test_ownerSharesWithNonexistentUsers_doesNotUpdateModelMetadata(self, client):
        client.post('/shareModel', data={
            'user': 'test',
            'modelName': 'test_voltageDrop',
            'email': ['nonexistent-user']
        })
        filepath = "data/Model/test/test_voltageDrop/allInputData.json"
        with open(filepath) as f:
            model_metadata = json.load(f)
        assert model_metadata.get('viewers') is None

    def test_ownerSharesWithNonexistentUsers_doesNotUpdateUserMetadata(self, client):
        fake_user = 'nonexistent-user'
        client.post('/shareModel', data={
            'user': 'test',
            'modelName': 'test_voltageDrop',
            'email': [fake_user]
        })
        fake_filepath = 'data/User/' + fake_user + '.json'
        real_filepath = 'data/User/test.json'
        assert os.path.isfile(fake_filepath) == False
        assert os.path.isfile(real_filepath) == True

    def test_ownerRevokesFromNonexistentUsers_doesNotUpdateModelMetadata(self, client):
        """Nonexistant user was never shared with in the first place"""
        pass

    def test_ownerRevokesFromNonexistentUsers_doesNotUpdateUserMetadata(self, client):
        """username.json file does not exist"""
        pass

    def test_ownerSharesWithAdmin_doesNotUpdateModelMetadata(self, client):
        client.post('/shareModel', data={
            'user': 'test',
            'modelName': 'test_voltageDrop',
            'email': ['admin']
        })
        filepath = "data/Model/test/test_voltageDrop/allInputData.json"
        with open(filepath) as f:
            model_metadata = json.load(f)
        assert model_metadata.get('viewers') is None


    def test_ownerSharesWithAdmin_doesNotUpdateUserMetadata(self, client):
        client.post('/shareModel', data={
            'user': 'test',
            'modelName': 'test_voltageDrop',
            'email': ['admin']
        })
        filepath = 'data/User/admin.json'
        with open(filepath) as f:
            user_metadata = json.load(f)
        assert user_metadata.get('readonly_models') is None

    def test_ownerSharesWithSelf_doesNotUpdateModelMetadata(self, client):
        client.post('/shareModel', data={
            'user': 'test',
            'modelName': 'test_voltageDrop',
            'email': ['test']
        })
        filepath = "data/Model/test/test_voltageDrop/allInputData.json"
        with open(filepath) as f:
            model_metadata = json.load(f)
        assert model_metadata.get('viewers') is None

    def test_ownerSharesWithSelf_doesNotUpdateUserMetadata(self, client):
        client.post('/shareModel', data={
            'user': 'test',
            'modelName': 'test_voltageDrop',
            'email': ['test']
        })
        filepath = 'data/User/test.json'
        with open(filepath) as f:
            user_metadata = json.load(f)
        assert user_metadata.get('readonly_models') is None
    

    def test_ownerSharesThenRunsModel_persistsModelMetadataChanges(self, client):
        client.post('/shareModel', data={
            'user': 'test',
            'modelName': 'test_voltageDrop',
            'email': ['first-test-user', 'second-test-user']
        })
        model_dir = os.path.join(omfDir, 'data/Model/test/test_voltageDrop')
        model_metadata_path = os.path.join(model_dir, 'allInputData.json')
        with open(model_metadata_path) as f:
            form_data = json.load(f)
        assert sorted(form_data.get('viewers')) == sorted(['first-test-user', 'second-test-user'])
        # The 'user' and 'modelName' are added in renderTemplate() of __neoMetaModel__.py. restoreInputs() in omf.json is responsible for placing the
        # allInputData.json values into the HTML template. Then, the allInputData.json values are resubmitted to /runModel/ as pData through an HTML
        # form
        form_data['user'] = 'test'
        form_data['modelName'] = 'test_voltageDrop'
        with client as client:
            rv = client.post('/runModel/', data=form_data)
            assert rv.status_code == 302
            assert rv.headers.get("Location") == "http://localhost" + url_for('showModel', owner='test', modelName='test_voltageDrop')
        # Running the model is asynchronous!
        pid_filepath = os.path.join(model_dir, 'PPID.txt')
        while not os.path.isfile(pid_filepath):
            continue
        assert os.path.isfile(pid_filepath) is True
        while os.path.isfile(pid_filepath):
            continue
        with open(model_metadata_path) as f:
            model_metadata = json.load(f)
        assert sorted(model_metadata.get('viewers')) == sorted(['first-test-user', 'second-test-user'])


    def test_ownerSharesThenRunsModel_persistsUserMetadataChanges(self, client):
        client.post('/shareModel', data={
            'user': 'test',
            'modelName': 'test_voltageDrop',
            'email': ['first-test-user', 'second-test-user']
        })
        # Check user metadata state
        for filename in ['first-test-user.json', 'second-test-user.json']:
            filepath = "data/User/" + filename
            with open(filepath) as f:
                user_metadata = json.load(f)
                assert len(user_metadata.get('readonly_models')) == 1
                assert len(user_metadata.get('readonly_models').get('test')) == 1
                assert user_metadata.get('readonly_models').get('test')[0] == 'test_voltageDrop'
        model_dir = os.path.join(omfDir, 'data/Model/test/test_voltageDrop')
        model_metadata_path = os.path.join(model_dir, 'allInputData.json')
        with open(model_metadata_path) as f:
            form_data = json.load(f)
        form_data['user'] = 'test'
        form_data['modelName'] = 'test_voltageDrop'
        with client as client:
            rv = client.post('/runModel/', data=form_data)
            assert rv.status_code == 302
            assert rv.headers.get("Location") == "http://localhost" + url_for('showModel', owner='test', modelName='test_voltageDrop')
        # Running the model is asynchronous!
        pid_filepath = os.path.join(model_dir, 'PPID.txt')
        while not os.path.isfile(pid_filepath):
            continue
        assert os.path.isfile(pid_filepath) is True
        while os.path.isfile(pid_filepath):
            continue
        # Check user metadata state
        for filename in ['first-test-user.json', 'second-test-user.json']:
            filepath = "data/User/" + filename
            with open(filepath) as f:
                user_metadata = json.load(f)
                assert len(user_metadata.get('readonly_models')) == 1
                assert len(user_metadata.get('readonly_models').get('test')) == 1
                assert user_metadata.get('readonly_models').get('test')[0] == 'test_voltageDrop'

    def test_ownerSharesWithValidAndInvalidUsers_doesNotUpdateModelMetadata(self, client):
        client.post('/shareModel', data={
            'user': 'test',
            'modelName': 'test_voltageDrop',
            'email': ['second-test-user', 'first-test-user', 'nonexistent-user']
        })
        filepath = "data/Model/test/test_voltageDrop/allInputData.json"
        with open(filepath) as f:
            model_metadata = json.load(f)
        assert model_metadata.get('viewers') is None

    def test_ownerSharesWithValidAndInvalidUsers_doesNotUpdateUserMetadata(self, client):
        client.post('/shareModel', data={
            'user': 'test',
            'modelName': 'test_voltageDrop',
            'email': ['second-test-user', 'first-test-user', 'nonexistent-user']
        })
        for filename in ['first-test-user.json', 'second-test-user.json', 'nonexistent-user.json']:
            filepath = "data/User/" + filename
            if os.path.isfile(filepath):
                with open(filepath) as f:
                    user_metadata = json.load(f)
                    assert user_metadata.get('readonly_models') is None

    def test_ownerSharesWhileModelIsRunning_doesNotUpdateModelMetadata(self, client):
        model_dir = os.path.join(omfDir, 'data/Model/test/test_voltageDrop')
        model_metadata_path = os.path.join(model_dir, 'allInputData.json')
        with open(model_metadata_path) as f:
            form_data = json.load(f)
        form_data['user'] = 'test'
        form_data['modelName'] = 'test_voltageDrop'
        with client as client:
            rv = client.post('/runModel/', data=form_data)
            assert rv.status_code == 302
            assert rv.headers.get("Location") == "http://localhost" + url_for('showModel', owner='test', modelName='test_voltageDrop')
        # Running the model is asynchronous!
        pid_filepath = os.path.join(model_dir, 'PPID.txt')
        while not os.path.isfile(pid_filepath):
            continue
        assert os.path.isfile(pid_filepath) is True
        rv = client.post('/shareModel', data={
            'user': 'test',
            'modelName': 'test_voltageDrop',
            'email': ['first-test-user', 'second-test-user']
        })
        assert rv.status_code == 409
        assert os.path.isfile(pid_filepath) is True
        with open(model_metadata_path) as f:
            model_metadata = json.load(f)
        assert model_metadata.get('viewers') is None

    def test_ownerSharesWhileModelIsRunning_doesNotUpdateUserMetadata(self, client):
        model_dir = os.path.join(omfDir, 'data/Model/test/test_voltageDrop')
        model_metadata_path = os.path.join(model_dir, 'allInputData.json')
        with open(model_metadata_path) as f:
            form_data = json.load(f)
        form_data['user'] = 'test'
        form_data['modelName'] = 'test_voltageDrop'
        with client as client:
            rv = client.post('/runModel/', data=form_data)
            assert rv.status_code == 302
            assert rv.headers.get("Location") == "http://localhost" + url_for('showModel', owner='test', modelName='test_voltageDrop')
        # Running the model is asynchronous!
        pid_filepath = os.path.join(model_dir, 'PPID.txt')
        while not os.path.isfile(pid_filepath):
            continue
        assert os.path.isfile(pid_filepath) is True
        rv = client.post('/shareModel', data={
            'user': 'test',
            'modelName': 'test_voltageDrop',
            'email': ['first-test-user', 'second-test-user']
        })
        assert rv.status_code == 409
        assert os.path.isfile(pid_filepath) is True
        for filename in ['first-test-user.json', 'second-test-user.json']:
            filepath = "data/User/" + filename
            if os.path.isfile(filepath):
                with open(filepath) as f:
                    user_metadata = json.load(f)
                    assert user_metadata.get('readonly_models') is None

    def test_ownerRevokesViewershipFromNonexistentUser_updatesModelMetadata(self, client):
        """
        It's possible that a model owner can share with a user, and then that user can be deleted. In such a case, the allInputData.json file should
        be able to be updated to remove such a deleted user.
        """
        rv = client.post('/shareModel', data={
            'user': 'test',
            'modelName': 'test_voltageDrop',
            'email': ['first-test-user', 'second-test-user']
        })
        assert rv.status_code == 200
        with open(os.path.join(omfDir, 'data/Model/test/test_voltageDrop/allInputData.json')) as f:
            model_metadata = json.load(f)
            assert sorted(model_metadata.get('viewers')) == sorted(['first-test-user', 'second-test-user'])
        os.remove(os.path.join(omfDir, 'data/User', 'first-test-user.json'))
        rv = client.post('/shareModel', data={
            'user': 'test',
            'modelName': 'test_voltageDrop',
            'email': ['second-test-user']
        })
        assert rv.status_code == 200
        with open(os.path.join(omfDir, 'data/Model/test/test_voltageDrop/allInputData.json')) as f:
            model_metadata = json.load(f)
            assert model_metadata.get('viewers') == ['second-test-user']