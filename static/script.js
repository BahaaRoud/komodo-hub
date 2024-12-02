document.getElementById('registerUserForm').addEventListener('submit', async function(event) {
    event.preventDefault();  // Prevent the default form submission

    // Get form data
    const username = document.getElementById('username').value;
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const role = document.getElementById('role').value;
    const accessCode = document.getElementById('accessCode').value;
    const organizationCode = document.getElementById('organization_id').value;

    const payload = {
        username: username,
        email: email,
        password: password,
        role: role,
        accessCode: accessCode,  // Include the access code in the payload
        organization_code: organizationCode
    };

    // Access code check
    //const restrictedRoles = ['Admin', 'Teacher', 'Student', 'Regular'];
    //if (restrictedRoles.includes(role) && accessCode === '') {
     //   document.getElementById('message').textContent = "Access code is required for " + role;
       // document.getElementById('message').style.color = 'red';
        //return;
    //}

    try {
        // Send POST request to the backend API
        const response = await fetch('http://127.0.0.1:5000/register_user', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        const result = await response.json();

        const messageDiv = document.getElementById('message');
        if (response.ok) {
            messageDiv.style.color = 'green';
            messageDiv.textContent = result.message || 'User registered successfully!';
        } else {
            messageDiv.style.color = 'red';
            messageDiv.textContent = result.message || 'Error occurred while registering.';
        }

    } catch (error) {
        const messageDiv = document.getElementById('message');
        messageDiv.style.color = 'red';
        messageDiv.textContent = 'An unexpected error occurred. Please try again.';
    }
});

// Role and Access Code Toggle Logic
const rolesByOrgType = {
    "School": ["Admin", "Teacher", "Student"],
    "General Org": ["Admin", "Regular"],
    "None": ["Community Member"]
};

document.getElementById('organization').addEventListener('change', function() {
    // Get selected organization type from data attribute
    const selectedOrgType = this.options[this.selectedIndex].getAttribute('data-org-type');
    const roleSelect = document.getElementById('role');
    const accessCodeField = document.getElementById('accessCodeField');

    // Populate roles based on selected organization type
    roleSelect.innerHTML = "";
    const roles = rolesByOrgType[selectedOrgType] || rolesByOrgType["None"];
    roles.forEach(role => {
        const option = document.createElement('option');
        option.value = role;
        option.textContent = role;
        roleSelect.appendChild(option);
    });

    // Trigger the access code toggle based on default role
    toggleAccessCodeField();
});

// Show/Hide access code field based on selected role
document.getElementById('role').addEventListener('change', toggleAccessCodeField);

function toggleAccessCodeField() {
    const restrictedRoles = ['Admin', 'Teacher', 'Student', 'Regular'];
    const selectedRole = document.getElementById('role').value;
    const accessCodeField = document.getElementById('accessCodeField');

    // Show the access code field if the selected role is restricted, otherwise hide it
    if (restrictedRoles.includes(selectedRole)) {
        accessCodeField.style.display = 'block';
    } else {
        accessCodeField.style.display = 'none';
    }
}
document.addEventListener('DOMContentLoaded', function () {
    const orgTypeElement = document.getElementById('organization');
    const orgCodeDiv = document.getElementById('org_code_div');
    const roleSelect = document.getElementById('role');
    const accessCodeField = document.getElementById('accessCodeField');

    function updateFormFields() {
        const orgType = orgTypeElement.options[orgTypeElement.selectedIndex].getAttribute('data-org-type');

        // Show or hide organization code field
        orgCodeDiv.style.display = orgType === 'None' ? 'none' : 'block';

        // Populate roles based on organization type
        roleSelect.innerHTML = '<option value="">Select Role</option>';
        if (orgType === 'School') {
            roleSelect.innerHTML += `
                <option value="Admin">Admin</option>
                <option value="Teacher">Teacher</option>
                <option value="Student">Student</option>
            `;
        } else if (orgType === 'General Org') {
            roleSelect.innerHTML += `
                <option value="Admin">Admin</option>
                <option value="User">User</option>
            `;
        } else {
            roleSelect.innerHTML += '<option value="General User">Public User</option>';
        }

        // Hide the access code field initially
        accessCodeField.style.display = 'none';
    }

    function toggleAccessCodeField() {
        const role = roleSelect.value;
        const restrictedRoles = ['Admin', 'Teacher', 'Student', 'User'];

        // Show or hide the access code field based on the selected role
        if (restrictedRoles.includes(role)) {
            accessCodeField.style.display = 'block';
        } else {
            accessCodeField.style.display = 'none';
        }
    }

    // Attach event listeners
    orgTypeElement.addEventListener('change', updateFormFields);
    roleSelect.addEventListener('change', toggleAccessCodeField);

    // Initialize form fields
    updateFormFields();
});