import smartpy as sp

class Lottery(sp.Contract):
    def __init__(self,_admin):
        self.init(
            players = sp.map(l={}, tkey=sp.TNat, tvalue=sp.TAddress),
            ticket_cost = sp.tez(1),
            tickets_available = sp.nat(3),
            max_tickets = sp.nat(3),
            admin = _admin,
        )
    
    @sp.entry_point
    def buy_ticket(self, ticket_count):
        sp.set_type(ticket_count, sp.TNat)

        # Sanity checks
        sp.verify(self.data.tickets_available > 0, "NO TICKETS AVAILABLE")
        sp.verify(sp.amount >= sp.mul(self.data.ticket_cost, ticket_count), "INVALID AMOUNT")

        # Storage updates
        self.data.players[sp.len(self.data.players)] = sp.sender
        self.data.tickets_available = sp.as_nat(self.data.tickets_available - ticket_count)

        # Return extra tez balance to the sender
        extra_balance = sp.amount - sp.mul(self.data.ticket_cost, ticket_count)
        sp.if extra_balance > sp.mutez(0):
            sp.send(sp.sender, extra_balance)

    @sp.entry_point
    def end_game(self, random_number):
        sp.set_type(random_number, sp.TNat)

        # Sanity checks
        sp.verify(sp.sender == self.data.admin, "NOT_AUTHORISED")
        sp.verify(self.data.tickets_available == 0, "GAME IS YET TO END")

        # Pick a winner
        winner_id = random_number % self.data.max_tickets
        winner_address = self.data.players[winner_id]

        # Send the reward to the winner
        sp.send(winner_address, sp.balance)

        # Reset the game
        self.data.players = {}
        self.data.tickets_available = self.data.max_tickets

    @sp.entry_point
    def change_ticket_cost(self, new_ticket_cost):
        sp.set_type(new_ticket_cost, sp.TMutez)

        sp.verify(sp.sender == self.data.admin, "NOT_AUTHORISED")
        sp.verify(self.data.tickets_available == self.data.max_tickets, "A GAME IS ONGOING")

        self.data.ticket_cost = new_ticket_cost

    @sp.entry_point
    def change_max_tickets(self, new_max_tickets):
        sp.set_type(new_max_tickets, sp.TNat)

        sp.verify(sp.sender == self.data.admin, "NOT_AUTHORISED")
        sp.verify(self.data.tickets_available == self.data.max_tickets, "A GAME IS ONGOING")

        self.data.max_tickets = new_max_tickets

    @sp.entry_point
    def default(self):
        sp.failwith("NOT ALLOWED")

@sp.add_test(name = "main")
def test():
    scenario = sp.test_scenario()

    # Test accounts
    admin = sp.test_account("admin")
    alice = sp.test_account("alice")
    bob = sp.test_account("bob")
    mike = sp.test_account("mike")

    # Contract instance
    lottery = Lottery(admin.address)
    scenario += lottery

    # buy_ticket
    scenario.h2("buy_ticket (valid test)")
    scenario += lottery.buy_ticket(1).run(amount = sp.tez(1), sender = alice)
    scenario += lottery.buy_ticket(2).run(amount = sp.tez(2), sender = bob)

    scenario.h2("buy_ticket (failure test)")
    scenario += lottery.buy_ticket(1).run(amount = sp.tez(1), sender = alice, valid = False)

    # end_game
    scenario.h2("end_game (valid test)")
    scenario += lottery.end_game(21).run(sender = admin)

    # change ticket cost
    scenario.h2("change_ticket_cost (valid test)")
    scenario += lottery.change_ticket_cost(sp.tez(2)).run(sender = admin)

    # change max tickets
    scenario.h2("change_max_tickets (valid test)")
    scenario += lottery.change_max_tickets(5).run(sender = admin)
    