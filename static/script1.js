// script.js

// Global Variables
let expenses = [];
let expenseHistory = [];

// DOM Elements
const logoutBtn = document.getElementById("logoutBtn");
const expenseTableBody = document.querySelector("#expenseTable tbody");
const totalAmountElement = document.getElementById("totalAmount");

// Event Listeners
if (logoutBtn) {
    logoutBtn.addEventListener("click", function(e) {
        e.preventDefault();
        window.location.href = "/logout";
    });
}

// Expense Handling Functions
function addExpense(event) {
    event.preventDefault();

    const expenseName = document.getElementById("expenseName").value;
    const expenseAmount = parseFloat(document.getElementById("expenseAmount").value);
    const expenseCategory = document.getElementById("expenseCategory").value;

    if (!expenseName || isNaN(expenseAmount) || expenseAmount <= 0) {
        alert("Please enter valid expense details.");
        return;
    }

    // Add to expenses
    const expense = {
        name: expenseName,
        amount: expenseAmount,
        category: expenseCategory,
        date: new Date().toLocaleString(),
    };
    expenses.push(expense);

    // Add to expense history
    expenseHistory.push(expense);

    // Reset form
    expenseForm.reset();

    // Update the expense table and total amount
    updateExpenseTable();
    updateTotalAmount();
    updateHistoryTable();
}

function updateExpenseTable() {
    expenseTableBody.innerHTML = "";

    expenses.forEach((expense, index) => {
        const row = document.createElement("tr");

        row.innerHTML = `
            <td>${expense.name}</td>
            <td>$${expense.amount.toFixed(2)}</td>
            <td>${expense.category}</td>
            <td>
                <button onclick="deleteExpense(${index})">Delete</button>
            </td>
        `;
        expenseTableBody.appendChild(row);
    });
}

function updateHistoryTable() {
    historyTableBody.innerHTML = "";

    expenseHistory.forEach((expense) => {
        const row = document.createElement("tr");

        row.innerHTML = `
            <td>${expense.name}</td>
            <td>$${expense.amount.toFixed(2)}</td>
            <td>${expense.category}</td>
            <td>${expense.date}</td>
            <td>
                <button onclick="deleteHistoryExpense(${expenseHistory.indexOf(expense)})">Delete</button>
            </td>
        `;
        historyTableBody.appendChild(row);
    });
}

function updateTotalAmount() {
    const amounts = Array.from(expenseTableBody.querySelectorAll('td:nth-child(3)')).map(td => 
        parseFloat(td.textContent.replace('$', ''))
    );
    const total = amounts.reduce((sum, amount) => sum + amount, 0);
    if (totalAmountElement) {
        totalAmountElement.textContent = `$${total.toFixed(2)}`;
    }
}

// Delete Expense Function
function deleteExpense(expenseId) {
    if (confirm('Are you sure you want to delete this expense?')) {
        fetch(`/delete_expense/${expenseId}`, {
            method: 'DELETE',
        })
        .then(response => {
            if (response.ok) {
                window.location.reload();
            } else {
                alert('Error deleting expense');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error deleting expense');
        });
    }
}

function deleteHistoryExpense(index) {
    expenseHistory.splice(index, 1);
    updateHistoryTable();
}

// Edit Expense Function
function editExpense(expenseId) {
    window.location.href = `/edit_expense/${expenseId}`;
}

// Set today's date when page loads
document.addEventListener('DOMContentLoaded', function() {
    const dateInput = document.getElementById('date');
    if (dateInput) {
        const today = new Date().toISOString().split('T')[0];
        dateInput.value = today;
    }

    // Handle delete buttons
    document.querySelectorAll('.btn-delete').forEach(button => {
        button.addEventListener('click', function() {
            if (confirm('Are you sure you want to delete this expense?')) {
                const expenseId = this.dataset.id;
                fetch(`/delete_expense/${expenseId}`, {
                    method: 'DELETE'
                })
                .then(response => response.json())
                .then(data => {
                    if (data.message) {
                        // Remove the row from the table
                        this.closest('tr').remove();
                        // Optionally refresh the page to update totals
                        window.location.reload();
                    }
                })
                .catch(error => console.error('Error:', error));
            }
        });
    });

    // Handle edit buttons
    document.querySelectorAll('.btn-edit').forEach(button => {
        button.addEventListener('click', function() {
            const expenseId = this.dataset.id;
            window.location.href = `/edit_expense/${expenseId}`;
        });
    });
});