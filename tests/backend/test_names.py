import pytest
from names import DistinguishedName, Hierarchy


@pytest.fixture
def simple_names():
    yield [
        "CN=First Wonderland CA, OU=Data center, C=WN, O=The Corporation",
        "CN=Workshop Node, O=Workshop, C=WN",
        "CN=Cat's house Node, STREET=Cat's house, L=Cheshire, C=WN",
        "CN=Node admin, STREET=Cat's house, L=Cheshire, C=WN",
        "CN=Cheshire cat, STREET=Cat's house, L=Cheshire, C=WN"
    ]


@pytest.fixture
def combined_names():
    yield [
        "CN=First Wonderland CA+DC=ca01, OU=Data center, C=WN+DC=wonderland, O=The Corporation+DC=thecorp",
        "CN=Workshop Node+DC=node01, O=Workshop+DC=workshop, C=WN+DC=wonderland",
        "CN=Cat's house Node+DC=catsnode, STREET=Cat's house, L=Cheshire, C=WN+DC=wonderland",
        "CN=Node admin+UID=admin, DC=catsnode, STREET=Cat's house, L=Cheshire, C=WN+DC=wonderland",
        "CN=Cheshire cat+UID=checat, STREET=Cat's house, L=Cheshire, C=WN+DC=wonderland"
    ]


@pytest.fixture
def domain_hierarchies():
    yield [
        "DC=ca01, DC=wonderland, DC=thecorp",
        "DC=node01, DC=workshop, DC=wonderland",
        "DC=catsnode, DC=wonderland",
        "UID=admin, DC=catsnode, DC=wonderland",
        "UID=checat, DC=wonderland",
    ]


@pytest.fixture
def country_hierarchies():
    yield [
        "CN=First Wonderland CA, C=WN",
        "CN=Workshop Node, C=WN",
        "CN=Cat's house Node, STREET=Cat's house, L=Cheshire, C=WN",
        "CN=Node admin, STREET=Cat's house, L=Cheshire, C=WN",
        "CN=Cheshire cat, STREET=Cat's house, L=Cheshire, C=WN",
    ]


@pytest.fixture
def organization_hierarchies():
    yield [
        "CN=First Wonderland CA, OU=Data center, O=The Corporation",
        "CN=Workshop Node, O=Workshop",
        None,
        None,
        None,
    ]


@pytest.fixture
def base_domain_hierarchies():
    yield [
        "DC=ca01, DC=wonderland, DC=thecorp",
        "DC=node01, DC=workshop, DC=wonderland",
        "DC=catsnode, DC=wonderland",
        "DC=catsnode, DC=wonderland",
        "DC=wonderland"
    ]


@pytest.fixture
def base_country_hierarchies():
    yield [
        "C=WN",
        "C=WN",
        "STREET=Cat's house, L=Cheshire, C=WN",
        "STREET=Cat's house, L=Cheshire, C=WN",
        "STREET=Cat's house, L=Cheshire, C=WN"
    ]


@pytest.fixture
def base_organization_hierarchies():
    yield [
        "OU=Data center, O=The Corporation",
        "O=Workshop",
        None,
        None,
        None,
    ]


def test_simple_names(simple_names):
    raw_r = list()
    for N in range(len(simple_names)):
        dn_name = DistinguishedName(simple_names[N])
        raw_r.append(dn_name._raw)
    assert raw_r == [
        ((('CN', 'First Wonderland CA'),), (('OU', 'Data center'),), (('C', 'WN'),), (('O', 'The Corporation'),)),
        ((('CN', 'Workshop Node'),), (('O', 'Workshop'),), (('C', 'WN'),)),
        ((('CN', "Cat's house Node"),), (('STREET', "Cat's house"),), (('L', 'Cheshire'),), (('C', 'WN'),)),
        ((('CN', 'Node admin'),), (('STREET', "Cat's house"),), (('L', 'Cheshire'),), (('C', 'WN'),)),
        ((('CN', 'Cheshire cat'),), (('STREET', "Cat's house"),), (('L', 'Cheshire'),), (('C', 'WN'),))
    ]
    for N in range(len(raw_r)):
        if raw_r[N]:
            assert simple_names[N].replace(', ', ',') == str(DistinguishedName(raw_r[N]))


def test_combined_names(combined_names,
                        base_domain_hierarchies, base_country_hierarchies, base_organization_hierarchies):
    raw_r = list()
    for N in range(len(combined_names)):
        dn_name = DistinguishedName(combined_names[N])
        raw_r.append(dn_name._raw)
    assert raw_r == [
        ((('CN', 'First Wonderland CA'), ('DC', 'ca01')), (('OU', 'Data center'),), (('C', 'WN'), ('DC', 'wonderland')),
         (('O', 'The Corporation'), ('DC', 'thecorp'))),
        ((('CN', 'Workshop Node'), ('DC', 'node01')), (('O', 'Workshop'), ('DC', 'workshop')),
         (('C', 'WN'), ('DC', 'wonderland'))),
        ((('CN', "Cat's house Node"), ('DC', 'catsnode')), (('STREET', "Cat's house"),), (('L', 'Cheshire'),),
         (('C', 'WN'), ('DC', 'wonderland'))),
        ((('CN', 'Node admin'), ('UID', 'admin')), (('DC', 'catsnode'),), (('STREET', "Cat's house"),),
         (('L', 'Cheshire'),), (('C', 'WN'), ('DC', 'wonderland'))),
        ((('CN', 'Cheshire cat'), ('UID', 'checat')), (('STREET', "Cat's house"),),
         (('L', 'Cheshire'),), (('C', 'WN'), ('DC', 'wonderland')))
    ]
    for N in range(len(raw_r)):
        assert combined_names[N].replace(', ', ',') == str(DistinguishedName(raw_r[N]))
        assert (base_domain_hierarchies[N] is None or
                (DistinguishedName(base_domain_hierarchies[N]) ==
                 DistinguishedName(raw_r[N]).extract(Hierarchy.Domain, True)))
        assert (base_country_hierarchies[N] is None or
                (DistinguishedName(base_country_hierarchies[N]) ==
                 DistinguishedName(raw_r[N]).extract(Hierarchy.Country, True)))
        assert (base_organization_hierarchies[N] is None or
                (DistinguishedName(base_organization_hierarchies[N]) ==
                 DistinguishedName(raw_r[N]).extract(Hierarchy.Organization, True)))


def test_domain_hierarchies(domain_hierarchies, combined_names):
    raw_r = list()
    rest = list()
    for N in range(len(domain_hierarchies)):
        if domain_hierarchies[N]:
            dn_name = DistinguishedName(domain_hierarchies[N])
            raw_r.append(dn_name._raw)
            rest.append(DistinguishedName(dn_name._raw))
    assert raw_r == [
        ((('DC', 'ca01'),), (('DC', 'wonderland'),), (('DC', 'thecorp'),)),
        ((('DC', 'node01'),), (('DC', 'workshop'),), (('DC', 'wonderland'),)),
        ((('DC', 'catsnode'),), (('DC', 'wonderland'),)),
        ((('UID', 'admin'),), (('DC', 'catsnode'),), (('DC', 'wonderland'),)),
        ((('UID', 'checat'),), (('DC', 'wonderland'),))
    ]
    for N in range(len(raw_r)):
        if raw_r[N]:
            assert domain_hierarchies[N].replace(', ', ',') == str(DistinguishedName(raw_r[N]))
            assert DistinguishedName(combined_names[N]).extract(Hierarchy.Domain) == DistinguishedName(raw_r[N])


def test_country_hierarchies(country_hierarchies, combined_names):
    raw_r = list()
    rest = list()
    for N in range(len(country_hierarchies)):
        if country_hierarchies[N]:
            dn_name = DistinguishedName(country_hierarchies[N])
            raw_r.append(dn_name._raw)
            rest.append(DistinguishedName(dn_name._raw))
    assert raw_r == [
        ((('CN', 'First Wonderland CA'),), (('C', 'WN'),)),
        ((('CN', 'Workshop Node'),), (('C', 'WN'),)),
        ((('CN', "Cat's house Node"),), (('STREET', "Cat's house"),), (('L', 'Cheshire'),), (('C', 'WN'),)),
        ((('CN', "Node admin"),), (('STREET', "Cat's house"),), (('L', 'Cheshire'),), (('C', 'WN'),)),
        ((('CN', "Cheshire cat"),), (('STREET', "Cat's house"),), (('L', 'Cheshire'),), (('C', 'WN'),))
    ]
    for N in range(len(raw_r)):
        if raw_r[N]:
            assert country_hierarchies[N].replace(', ', ',') == str(DistinguishedName(raw_r[N]))
            assert DistinguishedName(combined_names[N]).extract(Hierarchy.Country) == DistinguishedName(raw_r[N])


def test_organization_hierarchies(organization_hierarchies, combined_names):
    raw_r = list()
    for N in range(len(organization_hierarchies)):
        if organization_hierarchies[N]:
            dn_name = DistinguishedName(organization_hierarchies[N])
            raw_r.append(dn_name._raw)
        else:
            raw_r.append(None)
    assert raw_r == [
        ((('CN', 'First Wonderland CA'),), (('OU', 'Data center'),), (('O', 'The Corporation'),)),
        ((('CN', 'Workshop Node'),), (('O', 'Workshop'),)),
        None,
        None,
        None
    ]
    for N in range(len(raw_r)):
        if raw_r[N]:
            assert organization_hierarchies[N].replace(', ', ',') == str(DistinguishedName(raw_r[N]))
            assert DistinguishedName(combined_names[N]).extract(Hierarchy.Organization) == DistinguishedName(raw_r[N])
