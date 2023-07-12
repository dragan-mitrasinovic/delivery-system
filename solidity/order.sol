pragma solidity ^0.8.2;

contract Order {
    address payable public customer;
    address payable public courier;
    address payable public owner;
    uint256 public amountToPay;
    bool public paid = false;

    constructor(address payable _customer, uint256 _amountToPay) {
        customer = _customer;
        amountToPay = _amountToPay;
        owner = payable(msg.sender);
    }

    function setCourier(address payable _courier) public {
        courier = _courier;
    }

    function payOrder() public payable {
        require(msg.value >= amountToPay, "Insufficient funds.");
        require(!paid, "Transfer already complete.");
        paid = true;
    }

    function distributeFunds() public {
        require(paid, "Transfer not complete.");
        require(courier != address(0), "Delivery not complete.");

        uint256 amount = address(this).balance;
        uint256 courierShare = amount * 20 / 100;
        uint256 ownerShare = amount - courierShare;

        courier.transfer(courierShare);
        owner.transfer(ownerShare);
    }
}