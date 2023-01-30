import aws_cdk as core
import aws_cdk.assertions as assertions

from currency_exchange_tracking.currency_exchange_tracking_stack import CurrencyExchangeTrackingStack

# example tests. To run these tests, uncomment this file along with the example
# resource in currency_exchange_tracking/currency_exchange_tracking_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = CurrencyExchangeTrackingStack(app, "currency-exchange-tracking")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
