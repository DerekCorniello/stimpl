from typing import Any, Tuple, Optional

from stimpl.expression import *
from stimpl.types import *
from stimpl.errors import *

"""
Interpreter State
"""


class State(object):
    def __init__(self, variable_name: str, variable_value: Expr, variable_type: Type, next_state: 'State') -> None:
        self.variable_name = variable_name
        self.value = (variable_value, variable_type)
        self.next_state = next_state

    def copy(self) -> 'State':
        variable_value, variable_type = self.value
        return State(self.variable_name, variable_value, variable_type, self.next_state)

    def set_value(self, variable_name, variable_value, variable_type):
        return State(variable_name, variable_value, variable_type, self)

    def get_value(self, variable_name) -> Any:
        if variable_name == self.variable_name:
            return self.value
        else:
            return self.next_state.get_value(variable_name)
    def __repr__(self) -> str:
        return f"{self.variable_name}: {self.value}, " + repr(self.next_state)


class EmptyState(State):
    def __init__(self):
        pass

    def copy(self) -> 'EmptyState':
        return EmptyState()

    def get_value(self, variable_name) -> None:
        return None

    def __repr__(self) -> str:
        return ""


"""
Main evaluation logic!
"""


def evaluate(expression: Expr, state: State) -> Tuple[Optional[Any], Type, State]:
    match expression:
        case Ren():
            return (None, Unit(), state)

        case IntLiteral(literal=l):
            return (l, Integer(), state)

        case FloatingPointLiteral(literal=l):
            return (l, FloatingPoint(), state)

        case StringLiteral(literal=l):
            return (l, String(), state)

        case BooleanLiteral(literal=l):
            return (l, Boolean(), state)

        case Print(to_print=to_print):
            printable_value, printable_type, new_state = evaluate(
                to_print, state)

            match printable_type:
                case Unit():
                    print("Unit")
                case _:
                    print(f"{printable_value}")

            return (printable_value, printable_type, new_state)

        case Sequence(exprs=exprs) | Program(exprs=exprs):
            # Start with a clean slate on value and type, keep the state the same
            variable_value = None
            variable_type = Unit()
            new_state = state

            # For every expression passed, evaluate it and return the results
            for expr in exprs:
                variable_value, variable_type, new_state = evaluate(expr, new_state)

            return (variable_value, variable_type, new_state)
            

        case Variable(variable_name=variable_name):
            value = state.get_value(variable_name)
            if value == None:
                raise InterpSyntaxError(
                    f"Cannot read from {variable_name} before assignment.")
            variable_value, variable_type = value
            return (variable_value, variable_type, state)

        case Assign(variable=variable, value=value):

            value_result, value_type, new_state = evaluate(value, state)

            variable_from_state = new_state.get_value(variable.variable_name)
            _, variable_type = variable_from_state if variable_from_state else (
                None, None)

            if value_type != variable_type and variable_type != None:
                raise InterpTypeError(f"""Mismatched types for Assignment:
            Cannot assign {value_type} to {variable_type}""")

            new_state = new_state.set_value(
                variable.variable_name, value_result, value_type)
            return (value_result, value_type, new_state)

        case Add(left=left, right=right):
            result = 0
            left_result, left_type, new_state = evaluate(left, state)
            right_result, right_type, new_state = evaluate(right, new_state)

            if left_type != right_type:
                raise InterpTypeError(f"""Mismatched types for Add:
            Cannot add {left_type} to {right_type}""")

            match left_type:
                case Integer() | String() | FloatingPoint():
                    result = left_result + right_result
                case _:
                    raise InterpTypeError(f"""Cannot add {left_type}s""")

            return (result, left_type, new_state)

        case Subtract(left=left, right=right):
            # Give default value 0 to the result of the operation.
            result = 0
            # Evaluate the parameter values for their values and types.
            left_result, left_type, new_state = evaluate(left, state)
            right_result, right_type, new_state = evaluate(right, new_state)

            # Ensure that the types match. If not, raise a type error
            if left_type != right_type:
                raise InterpTypeError(f"""Mismatched types for Subtract:
            Cannot add {left_type} to {right_type}""")

            # If types are numbers, calculate and return the value, 
            # otherwise, there is another type error
            match left_type:
                case Integer() | FloatingPoint():
                    result = left_result - right_result
                case _:
                    raise InterpTypeError(f"""Cannot subtract {left_type}s""")

            return (result, left_type, new_state)
            

        case Multiply(left=left, right=right):
            # Give default value 0 to the result of the operation.
            result = 0
            # Evaluate the parameter values for their values and types.
            left_result, left_type, new_state = evaluate(left, state)
            right_result, right_type, new_state = evaluate(right, new_state)

            # Ensure that the types match. If not, raise a type error
            if left_type != right_type:
                raise InterpTypeError(f"""Mismatched types for Multiply:
            Cannot add {left_type} to {right_type}""")

            # If types are numbers, calculate and return the value, 
            # otherwise, there is another type error
            match left_type:
                case Integer() | FloatingPoint():
                    result = left_result * right_result
                case _:
                    raise InterpTypeError(f"""Cannot multiply {left_type}s""")

            return (result, left_type, new_state)

        case Divide(left=left, right=right):
            # Give default value 0 to the result of the operation.
            result = 0
            # Evaluate the parameter values for their values and types.
            left_result, left_type, new_state = evaluate(left, state)
            right_result, right_type, new_state = evaluate(right, new_state)

            # Ensure that the types match. If not, raise a type error
            if right_result == 0:
                raise InterpMathError("""Division by Zero Error""")

            if left_type != right_type:
                raise InterpTypeError(f"""Mismatched types for Divide:
            Cannot add {left_type} to {right_type}""")

            # If types are numbers, calculate and return the value, 
            # otherwise, there is another type error
            match left_type:
                case FloatingPoint():
                    result = left_result / right_result
                case Integer():
                    result = left_result // right_result
                case _:
                    raise InterpTypeError(f"""Cannot divide {left_type}s""")

            return (result, left_type, new_state)

        case And(left=left, right=right):
            left_value, left_type, new_state = evaluate(left, state)
            right_value, right_type, new_state = evaluate(right, new_state)

            if left_type != right_type:
                raise InterpTypeError(f"""Mismatched types for And:
            Cannot add {left_type} to {right_type}""")
            match left_type:
                case Boolean():
                    result = left_value and right_value
                case _:
                    raise InterpTypeError(
                        "Cannot perform logical and on non-boolean operands.")

            return (result, left_type, new_state)

        case Or(left=left, right=right):
            # Evaluate for the type and value of the two parameters
            left_value, left_type, new_state = evaluate(left, state)
            right_value, right_type, new_state = evaluate(right, new_state)

            # Ensure they are both type boolean, if they are, return 
            # the logical result. If not, raise a type error.
            if left_type != right_type:
                raise InterpTypeError(f"""Mismatched types for Or:
            Cannot add {left_type} to {right_type}""")
            match left_type:
                case Boolean():
                    result = left_value or right_value
                case _:
                    raise InterpTypeError(
                        "Cannot perform logical and on non-boolean operands.")

            return (result, left_type, new_state)
            

        case Not(expr=expr):
            # Evaluate the expression for a boolean value
            variable_value, variable_type, new_state = evaluate(expr, state)

            # Return the negation of the value if it is a boolean, otherwise, raise 
            # a type error
            if variable_type == Boolean():
                return ((not variable_value), Boolean(), new_state)
            else:
                raise InterpTypeError(
                    f"""Cannot perform 'Not' operator on type {variable_type}.""")
        
        case If(condition=condition, true=true, false=false):
            # Evaluate the condition first and ensure it is a boolean type.
            # If not, raise a type error
            variable_value, variable_type, new_state = evaluate(condition, state)            

            if variable_type != Boolean():
                raise InterpTypeError(   
                    f"""Cannot evaluate condition {variable_value} with type {variable_type}""")

            # If the condition is true, evaluate the true expression. If
            # not, evaluate the false expression.
            if variable_value:
                result, result_type, new_state = evaluate(true, new_state)
            else:
                result, result_type, new_state = evaluate(false, new_state)
            
            return(result, result_type, new_state)

        case Lt(left=left, right=right):
            left_value, left_type, new_state = evaluate(left, state)
            right_value, right_type, new_state = evaluate(right, new_state)

            result = None

            if left_type != right_type:
                raise InterpTypeError(f"""Mismatched types for Lt:
            Cannot compare {left_type} to {right_type}""")

            match left_type:
                case Integer() | Boolean() | String() | FloatingPoint():
                    result = left_value < right_value
                case Unit():
                    result = False
                case _:
                    raise InterpTypeError(
                        f"Cannot perform < on {left_type} type.")

            return (result, Boolean(), new_state)

        case Lte(left=left, right=right):
            # Evaluate the left and right operands for value and type
            left_value, left_type, new_state = evaluate(left, state)
            right_value, right_type, new_state = evaluate(right, new_state)

            # Initialize a value for the result and type check the parameters
            result = None

            if left_type != right_type:
                raise InterpTypeError(f"""Mismatched types for Lte:
            Cannot compare {left_type} to {right_type}""")

            match left_type:
                case Integer() | Boolean() | String() | FloatingPoint():
                    result = left_value <= right_value
                case Unit():
                    result = True
                case _:
                    raise InterpTypeError(
                        f"Cannot perform <= on {left_type} type.")
            return (result, Boolean(), new_state)
            

        case Gt(left=left, right=right):
            # Evaluate the left and right operands for value and type
            left_value, left_type, new_state = evaluate(left, state)
            right_value, right_type, new_state = evaluate(right, new_state)

            # Initialize a value for the result and type check the parameters
            result = None

            if left_type != right_type:
                raise InterpTypeError(f"""Mismatched types for Gt:
            Cannot compare {left_type} to {right_type}""")

            match left_type:
                case Integer() | Boolean() | String() | FloatingPoint():
                    result = left_value > right_value
                case Unit():
                    result = False
                case _:
                    raise InterpTypeError(
                        f"Cannot perform > on {left_type} type.")

            return (result, Boolean(), new_state)

        case Gte(left=left, right=right):
            # Evaluate the left and right operands for value and type
            left_value, left_type, new_state = evaluate(left, state)
            right_value, right_type, new_state = evaluate(right, new_state)

            # Initialize a value for the result and type check the parameters
            result = None

            if left_type != right_type:
                raise InterpTypeError(f"""Mismatched types for Gte:
            Cannot compare {left_type} to {right_type}""")

            match left_type:
                case Integer() | Boolean() | String() | FloatingPoint():
                    result = left_value >= right_value
                case Unit():
                    result = True
                case _:
                    raise InterpTypeError(
                        f"Cannot perform >= on {left_type} type.")
            return (result, Boolean(), new_state)

        case Eq(left=left, right=right):
            # Evaluate the left and right operands for value and type
            left_value, left_type, new_state = evaluate(left, state)
            right_value, right_type, new_state = evaluate(right, new_state)

            # Type check the parameters
            if left_type != right_type:
                raise InterpTypeError(f"""Mismatched types for Gte:
            Cannot compare {left_type} to {right_type}""")

            if(left_type == Unit()):
                return(True, Boolean(), new_state)
            
            return ((left_value == right_value), Boolean(), new_state)        

        case Ne(left=left, right=right):
            # Evaluate the left and right operands for value and type
            left_value, left_type, new_state = evaluate(left, state)
            right_value, right_type, new_state = evaluate(right, new_state)

            # Type check the parameters
            if left_type != right_type:
                raise InterpTypeError(f"""Mismatched types for Gte:
            Cannot compare {left_type} to {right_type}""")
        
            if(left_type == Unit()):
                return(False, Boolean(), new_state)
            
            return ((left_value != right_value), Boolean(), new_state)    
            

        case While(condition=condition, body=body):
            if_cond_value, if_cond_type, new_state = evaluate(condition, state)
            result_type = Unit()

            if if_cond_type != Boolean():
                raise InterpTypeError(   
                    f"""Cannot evaluate condition with type {if_cond_type}""")

            while(if_cond_value):
                _, result_type, new_state = evaluate(body, new_state)
                if_cond_value, _, new_state = evaluate(condition, new_state)

            return (False, Boolean(), new_state)

        case _:
            raise InterpSyntaxError(f"Unhandled! error {expression}") ###CHANGE
    pass


def run_stimpl(program, debug=False):
    state = EmptyState()
    program_value, program_type, program_state = evaluate(program, state)

    if debug:
        print(f"program: {program}")
        print(f"final_value: ({program_value}, {program_type})")
        print(f"final_state: {program_state}")

    return program_value, program_type, program_state
