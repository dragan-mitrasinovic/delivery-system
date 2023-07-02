pragma solidity ^0.8.2;

contract Order {
    address payable public customer;
    bool public paid = false;

    constructor (address payable _customer) {
        customer = _customer;
    }
}