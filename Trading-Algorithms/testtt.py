
# defining truncate function
# second argument defaults to 0
# so that if no argument is passed
# it returns the integer part of number
 
def Is():
    if c >= b and c==b:
        index[1] = 1.5
        return
    
c,b = 1,1
        
        
    



index = [0.0] * len(range(10))

def fibonacci_sequence(n, price):
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    elif n == 2:
        return [0, 1]
    else:
        fib = [0, 1]
        for i in range(2, n):
            fib.append(fib[-1] + fib[-2])
        return [x / 100 * price for x in fib]

def set_stop_loss(price, n, trade_type):
    stop_loss = fibonacci_sequence(n, price)[-1]
    if trade_type == "buy":
        return price - stop_loss
    elif trade_type == "sell":
        return price + stop_loss
    else:
        return None


price = set_stop_loss(
    1.28558, 3, "buy")
print(price)