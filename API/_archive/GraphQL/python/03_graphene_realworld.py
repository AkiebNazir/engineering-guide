# REAL-WORLD EXAMPLE: Graphene (External 2)
# Demonstrates: Classic GraphQL ObjectTypes, Mutations, Context passing
from flask import Flask, request, abort
from flask_graphql import GraphQLView
import graphene

db_users = {"1": {"id": "1", "name": "Alice", "email": "alice@company.com"}}

class User(graphene.ObjectType):
    id = graphene.ID(required=True)
    name = graphene.String(required=True)
    email = graphene.String()
    
    # Custom resolver for a computed field
    is_corporate = graphene.Boolean()

    def resolve_is_corporate(parent, info):
        return "@company.com" in parent.email

class Query(graphene.ObjectType):
    user = graphene.Field(User, id=graphene.ID(required=True))

    def resolve_user(root, info, id):
        # Accessing HTTP context
        auth_header = info.context.headers.get("Authorization")
        if not auth_header:
            raise Exception("Unauthorized: Missing Token")
            
        data = db_users.get(id)
        if data:
            return User(**data)
        return None

class UpdateUserEmail(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        new_email = graphene.String(required=True)

    success = graphene.Boolean()
    user = graphene.Field(User)

    def mutate(root, info, id, new_email):
        if id not in db_users:
            return UpdateUserEmail(success=False, user=None)
        db_users[id]["email"] = new_email
        return UpdateUserEmail(success=True, user=User(**db_users[id]))

class Mutation(graphene.ObjectType):
    update_user_email = UpdateUserEmail.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)

app = Flask(__name__)
app.add_url_rule(
    '/graphql',
    view_func=GraphQLView.as_view(
        'graphql',
        schema=schema,
        graphiql=True # Enable GraphiQL UI
    )
)

if __name__ == "__main__":
    app.run(port=5000, debug=True)
